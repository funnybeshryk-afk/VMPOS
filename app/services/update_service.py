"""Avtomatik yangilash: GitHub Releases'dan yangi versiyani tekshirish,
yuklab olish, SHA-256 bilan tekshirish va o'rnatuvchini ishga tushirish.

Xavfsizlik qoidalari:
  * yuklab olish manzili FAQAT shu repozitoriyning release fayllari
    (https://github.com/<repo>/releases/download/...) bo'lishi shart;
  * o'rnatuvchi SHA-256 yig'indisi relizdagi qiymatga TENG bo'lmasa
    HECH QACHON ishga tushirilmaydi (yuklab olish buzilgan/uzilgan
    bo'lsa ham shu himoya ishlaydi);
  * hech qanday yig'indisi yo'q reliz yangilanish deb hisoblanmaydi.

Eslatma: SHA-256 relizning o'zidan olinadi — bu buzilgan yuklab
olishdan himoya qiladi, lekin GitHub akkaunti buzilgan holatdan emas.
Undan himoya — o'rnatuvchini kod imzosi (Authenticode) bilan imzolash.
"""

import hashlib
import json
import logging
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.version import APP_VERSION

logger = logging.getLogger(__name__)

REPO = "funnybeshryk-afk/VMPOS"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ALLOWED_DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"
# API ishlamasa (bloklangan / limit) zaxira yo'l: github.com'ning o'zi oxirgi
# tegga yo'naltiradi.
LATEST_PAGE_URL = f"https://github.com/{REPO}/releases/latest"



def is_allowed_download_url(url):
    """GitHub owner/repo nomida registr farqlamaydi (repo `VMPOS` deb
    ham, `vmpos` deb ham ochiladi), shuning uchun solishtirish registrga
    befarq — aks holda to'g'ri reliz ham rad etilib qolardi."""

    return isinstance(url, str) and url.lower().startswith(
        ALLOWED_DOWNLOAD_PREFIX.lower()
    )


INSTALLER_PATTERN = re.compile(r"^VMPOS-Setup-[0-9][0-9A-Za-z.\-]*\.exe$")

_API_TIMEOUT = 10
_DOWNLOAD_TIMEOUT = 30
_CHUNK_SIZE = 64 * 1024
_MAX_INSTALLER_BYTES = 500 * 1024 * 1024


class UpdateError(Exception):
    """Yangilash jarayonidagi kutilgan xato (foydalanuvchiga ko'rsatish
    mumkin). technical — qo'llab-quvvatlash uchun aniq sabab (logga ham
    yoziladi, oynada "Tafsilotlar"da ko'rinadi)."""

    def __init__(self, message, technical=""):
        super().__init__(message)
        self.technical = technical


class UpdateCancelled(UpdateError):
    pass


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    notes: str
    installer_name: str
    installer_url: str
    sha256: str
    size: int


def parse_version(text):
    """"v1.2.3" / "1.2" -> (1, 2, 3) / (1, 2). Noto'g'ri bo'lsa None."""

    if not isinstance(text, str):
        return None

    match = re.fullmatch(r"[vV]?(\d+(?:\.\d+){0,3})", text.strip())

    if match is None:
        return None

    return tuple(int(part) for part in match.group(1).split("."))


def _normalize(version_tuple):
    # (1, 2) va (1, 2, 0) teng hisoblansin.
    parts = list(version_tuple)

    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()

    return tuple(parts)


def is_newer(remote, current):
    remote_tuple = parse_version(remote)
    current_tuple = parse_version(current)

    if remote_tuple is None or current_tuple is None:
        return False

    return _normalize(remote_tuple) > _normalize(current_tuple)


def can_install():
    """O'rnatuvchini faqat Windows'dagi yig'ilgan (.exe) dasturda
    ishga tushiramiz — ishlab chiqish rejimida yangilanish ma'nosiz."""

    return sys.platform == "win32" and getattr(sys, "frozen", False)


def explain_network_error(error):
    """Tarmoq xatosini tushunarli sabab (foydalanuvchi uchun) va aniq
    texnik matnga (qo'llab-quvvatlash uchun) ajratadi."""

    technical = f"{type(error).__name__}: {error}"
    reason = getattr(error, "reason", None)

    if isinstance(error, urllib.error.HTTPError):
        code = error.code
        remaining = error.headers.get("X-RateLimit-Remaining") if error.headers else None

        if code in (403, 429) and remaining == "0":
            message = (
                "GitHub so'rovlar limiti tugadi (bitta tarmoqdan juda ko'p "
                "kompyuter so'ragan). Bir soatdan keyin urinib ko'ring."
            )
        elif code == 407:
            message = "Proxy-server login/parol so'rayapti (407)."
        elif code == 403:
            message = (
                "Kirish taqiqlangan (403): tarmoq (firewall/proxy) "
                "github.com'ni bloklagan bo'lishi mumkin."
            )
        elif code == 404:
            message = "Reliz topilmadi (404)."
        elif code >= 500:
            message = f"GitHub vaqtincha ishlamayapti (xato {code}). Keyinroq urinib ko'ring."
        else:
            message = f"Server xatosi: HTTP {code}."
    elif isinstance(reason, ssl.SSLError) or isinstance(error, ssl.SSLError):
        message = (
            "Xavfsiz ulanish (SSL) xatosi. Kompyuter sanasi va vaqti "
            "to'g'rimi? Antivirus yoki proxy sertifikatni almashtirayotgan "
            "bo'lishi mumkin."
        )
    elif isinstance(reason, socket.gaierror):
        message = (
            "Manzil topilmadi (DNS): tarmoqda internet yo'q yoki "
            "github.com bloklangan."
        )
    elif isinstance(reason, (socket.timeout, TimeoutError)) or isinstance(
        error, (socket.timeout, TimeoutError)
    ):
        message = (
            "Javob kelmadi (vaqt tugadi): tarmoq juda sekin yoki "
            "github.com bloklangan."
        )
    elif isinstance(reason, OSError) or isinstance(error, OSError):
        message = "Ulanish rad etildi (firewall yoki proxy to'sib qo'ygan bo'lishi mumkin)."
    else:
        message = "Serverga ulanib bo'lmadi."

    return message, technical


def _is_transient(error):
    reason = getattr(error, "reason", error)

    return isinstance(
        reason, (socket.timeout, TimeoutError, ConnectionResetError)
    )


def _open(url, timeout, attempts=2):
    """_request + bitta qayta urinish (vaqtinchalik uzilishlar uchun:
    vaqt tugashi, ulanish uzilishi). HTTP xatolari (403/404...) qayta
    urinilmaydi."""

    for attempt in range(attempts):
        try:
            return _request(url, timeout)
        except urllib.error.HTTPError:
            raise
        except Exception as error:
            if attempt + 1 < attempts and _is_transient(error):
                time.sleep(1)
                continue
            raise


def _extract_hash(text):
    match = re.search(r"\b([0-9a-fA-F]{64})\b", text)

    return match.group(1).lower() if match else None


def _request(url, timeout):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"VMPOS-updater/{APP_VERSION}",
            "Accept": "application/vnd.github+json, */*",
        },
    )

    return urllib.request.urlopen(request, timeout=timeout)


def _read_hash_file(url):
    with _open(url, _API_TIMEOUT) as response:
        text = response.read(4096).decode("utf-8", "replace")

    return _extract_hash(text)


def _extract_sha256(assets, installer_asset):
    digest = installer_asset.get("digest") or ""

    if digest.startswith("sha256:") and re.fullmatch(
        r"[0-9a-fA-F]{64}", digest[7:]
    ):
        return digest[7:].lower()

    hash_name = installer_asset["name"] + ".sha256"

    for asset in assets:
        if asset.get("name") == hash_name:
            url = asset.get("browser_download_url", "")

            if is_allowed_download_url(url):
                return _read_hash_file(url)

    return None


def parse_release(release, current_version=APP_VERSION):
    """GitHub release JSON -> UpdateInfo yoki None (yangilanish yo'q /
    reliz yaroqsiz). Tarmoqsiz, shuning uchun osongina sinaladi
    (SHA-256 relizdagi `digest` maydonidan yoki .sha256 faylidan)."""

    if release.get("draft") or release.get("prerelease"):
        return None

    tag = release.get("tag_name", "")

    if not is_newer(tag, current_version):
        return None

    assets = release.get("assets") or []

    installers = [
        asset for asset in assets
        if INSTALLER_PATTERN.match(asset.get("name", ""))
    ]

    if len(installers) != 1:
        logger.warning(
            "Relizda aynan bitta o'rnatuvchi bo'lishi kerak (%s): %s",
            len(installers),
            tag,
        )
        return None

    installer = installers[0]
    url = installer.get("browser_download_url", "")

    if not is_allowed_download_url(url):
        logger.warning("Ruxsat etilmagan yuklab olish manzili: %s", url)
        return None

    sha256 = _extract_sha256(assets, installer)

    if not sha256:
        logger.warning("Relizda SHA-256 yo'q, o'tkazib yuborildi: %s", tag)
        return None

    return UpdateInfo(
        version=tag.lstrip("vV"),
        notes=(release.get("body") or "").strip(),
        installer_name=installer["name"],
        installer_url=url,
        sha256=sha256,
        size=int(installer.get("size") or 0),
    )


def _check_via_redirect(current_version):
    """Zaxira yo'l: API o'rniga github.com/.../releases/latest sahifasi
    oxirgi relizning tegiga yo'naltiradi. Tarmoq ba'zan api.github.com'ni
    to'sadi (yoki limit tugaydi), lekin github.com'ni ochiq qoldiradi.
    Izoh (notes) bu yo'lda yo'q — yangilash esa xuddi shunday SHA-256
    tekshiruvi bilan ishlaydi."""

    with _open(LATEST_PAGE_URL, _API_TIMEOUT) as response:
        final_url = response.geturl()

    match = re.search(r"/releases/tag/([^/?#]+)$", final_url)

    if match is None:
        return None

    tag = match.group(1)

    if not is_newer(tag, current_version):
        return None

    version = tag.lstrip("vV")
    name = f"VMPOS-Setup-{version}.exe"

    if not INSTALLER_PATTERN.match(name):
        return None

    base = f"{ALLOWED_DOWNLOAD_PREFIX}{tag}/"

    try:
        sha256 = _read_hash_file(base + name + ".sha256")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            # Bu relizda bizning o'rnatuvchimiz yo'q (eski usuldagi reliz).
            logger.warning("Zaxira yo'l: %s relizida .sha256 yo'q", tag)
            return None
        raise

    if not sha256:
        logger.warning("Zaxira yo'l: %s uchun SHA-256 topilmadi", tag)
        return None

    return UpdateInfo(
        version=version,
        notes="",
        installer_name=name,
        installer_url=base + name,
        sha256=sha256,
        size=0,
    )


def check_for_update(current_version=APP_VERSION):
    """Yangi versiya bor bo'lsa UpdateInfo, yo'q bo'lsa None.

    Avval GitHub API, u ishlamasa — github.com orqali zaxira yo'l.
    Ikkalasi ham ishlamasa UpdateError (tushunarli sabab + texnik tafsilot)."""

    try:
        with _open(LATEST_RELEASE_URL, _API_TIMEOUT) as response:
            release = json.loads(response.read(2 * 1024 * 1024))

        return parse_release(release, current_version)

    except Exception as api_error:
        message, api_technical = explain_network_error(api_error)
        logger.warning("API orqali tekshirib bo'lmadi: %s", api_technical)

    try:
        return _check_via_redirect(current_version)

    except Exception as fallback_error:
        _message, fallback_technical = explain_network_error(fallback_error)
        logger.warning("Zaxira yo'l ham ishlamadi: %s", fallback_technical)

        raise UpdateError(
            f"Yangilanishni tekshirib bo'lmadi. {message}",
            technical=(
                f"GitHub API: {api_technical}\n"
                f"github.com: {fallback_technical}"
            ),
        ) from fallback_error


def verify_local_installer(path, current_version=APP_VERSION):
    """Internetsiz yangilash: o'rnatuvchi fayl (VMPOS-Setup-X.Y.Z.exe) va
    uning yonidagi .sha256 fayli. Hash MAJBURIY (fayl buzilmaganini va
    aynan reliz ekanini tekshirish uchun); eski versiyaga qaytishga ruxsat
    yo'q. Muvaffaqiyatda UpdateInfo qaytaradi."""

    path = Path(path)
    match = re.fullmatch(r"VMPOS-Setup-(\d+\.\d+\.\d+)\.exe", path.name)

    if match is None:
        raise UpdateError(
            "Fayl nomi VMPOS-Setup-X.Y.Z.exe ko'rinishida bo'lishi kerak "
            "(relizdan yuklab olingan nomni o'zgartirmang)."
        )

    version = match.group(1)

    if not is_newer(version, current_version):
        raise UpdateError(
            f"Bu versiya (v{version}) o'rnatilganidan (v{current_version}) "
            "yangi emas."
        )

    hash_path = path.with_name(path.name + ".sha256")

    if not hash_path.is_file():
        raise UpdateError(
            f"Yoniga {hash_path.name} faylini ham qo'ying (relizdan ikkalasini "
            "yuklab oling) — shunda fayl buzilmaganini tekshiramiz."
        )

    expected = _extract_hash(hash_path.read_text(encoding="utf-8", errors="replace"))

    if not expected:
        raise UpdateError(f"{hash_path.name} ichida SHA-256 topilmadi.")

    digest = hashlib.sha256()

    with open(path, "rb") as installer:
        for chunk in iter(lambda: installer.read(_CHUNK_SIZE), b""):
            digest.update(chunk)

    if digest.hexdigest() != expected:
        raise UpdateError(
            "Fayl buzilgan yoki boshqa fayl (SHA-256 mos kelmadi). "
            "Qayta yuklab oling."
        )

    return UpdateInfo(
        version=version,
        notes="",
        installer_name=path.name,
        installer_url=str(path),
        sha256=expected,
        size=path.stat().st_size,
    )


def download_installer(info, progress=None, is_cancelled=None):
    """O'rnatuvchini vaqtinchalik papkaga yuklaydi va SHA-256 ni
    tekshiradi. Mos kelmasa fayl o'chiriladi va UpdateError ko'tariladi."""

    if not is_allowed_download_url(info.installer_url):
        raise UpdateError("Ruxsat etilmagan yuklab olish manzili.")

    target_dir = Path(tempfile.mkdtemp(prefix="vmpos_update_"))
    target = target_dir / info.installer_name
    digest = hashlib.sha256()
    received = 0

    try:
        with _request(info.installer_url, _DOWNLOAD_TIMEOUT) as response:
            total = int(response.headers.get("Content-Length") or info.size or 0)

            with open(target, "wb") as out:
                while True:
                    if is_cancelled is not None and is_cancelled():
                        raise UpdateCancelled("Bekor qilindi.")

                    chunk = response.read(_CHUNK_SIZE)

                    if not chunk:
                        break

                    received += len(chunk)

                    if received > _MAX_INSTALLER_BYTES:
                        raise UpdateError("Fayl haddan tashqari katta.")

                    out.write(chunk)
                    digest.update(chunk)

                    if progress is not None:
                        progress(received, total)

        if digest.hexdigest() != info.sha256.lower():
            raise UpdateError(
                "Yuklab olingan fayl buzilgan (SHA-256 mos kelmadi). "
                "Yangilanish bekor qilindi."
            )

        return target

    except BaseException:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise


def launch_installer(installer_path):
    """O'rnatuvchini dasturdan MUSTAQIL jarayon sifatida ishga tushiradi.
    Chaqiruvchi shundan so'ng dasturni yopishi kerak (o'rnatuvchi
    ochiq exe faylni almashtira olmaydi)."""

    if not can_install():
        raise UpdateError(
            "Yangilash faqat o'rnatilgan dasturda (Windows) ishlaydi."
        )

    flags = 0

    if sys.platform == "win32":
        flags = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )

    subprocess.Popen(
        [
            str(installer_path),
            "/SILENT",
            "/NORESTART",
            "/SUPPRESSMSGBOXES",
            "/CLOSEAPPLICATIONS",
        ],
        close_fds=True,
        creationflags=flags,
    )
