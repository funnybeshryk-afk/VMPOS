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
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.version import APP_VERSION

logger = logging.getLogger(__name__)

REPO = "funnybeshryk-afk/VMPOS"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ALLOWED_DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"



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
    """Yangilash jarayonidagi kutilgan xato (foydalanuvchiga ko'rsatish mumkin)."""


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
    with _request(url, _API_TIMEOUT) as response:
        text = response.read(4096).decode("utf-8", "replace")

    match = re.search(r"\b([0-9a-fA-F]{64})\b", text)

    return match.group(1).lower() if match else None


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


def check_for_update(current_version=APP_VERSION):
    """Yangi versiya bor bo'lsa UpdateInfo, yo'q bo'lsa None.
    Tarmoq xatosida UpdateError ko'taradi."""

    try:
        with _request(LATEST_RELEASE_URL, _API_TIMEOUT) as response:
            release = json.loads(response.read(2 * 1024 * 1024))
    except Exception as error:
        raise UpdateError(f"Yangilanishni tekshirib bo'lmadi: {error}") from error

    return parse_release(release, current_version)


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
