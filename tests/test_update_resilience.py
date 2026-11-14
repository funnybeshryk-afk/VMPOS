import hashlib
import io
import socket
import ssl
import urllib.error
from email.message import Message

import pytest

from app.services import update_service as us
from app.services.update_service import UpdateError

PAYLOAD = b"installer-bytes" * 500
SHA = hashlib.sha256(PAYLOAD).hexdigest()


def http_error(code, **headers):
    msg = Message()
    for key, value in headers.items():
        msg[key.replace("_", "-")] = value
    return urllib.error.HTTPError("https://x", code, "err", msg, None)


# ---------------- sabablarni tushuntirish ----------------

@pytest.mark.parametrize("error,expected", [
    (http_error(403, X_RateLimit_Remaining="0"), "limiti tugadi"),
    (http_error(403), "bloklagan"),
    (http_error(407), "Proxy"),
    (http_error(404), "topilmadi"),
    (http_error(502), "vaqtincha"),
    (urllib.error.URLError(ssl.SSLError("bad cert")), "SSL"),
    (urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")), "DNS"),
    (urllib.error.URLError(socket.timeout("timed out")), "vaqt tugadi"),
    (TimeoutError("timed out"), "vaqt tugadi"),
    (urllib.error.URLError(ConnectionRefusedError(10061, "refused")), "rad etildi"),
    (ValueError("???"), "ulanib bo'lmadi"),
])
def test_network_errors_get_a_specific_human_reason(error, expected):
    message, technical = us.explain_network_error(error)

    assert expected.lower() in message.lower()
    assert type(error).__name__ in technical          # texnik matn aniq


# ---------------- zaxira yo'l ----------------

class Resp(io.BytesIO):
    def __init__(self, data=b"", url=""):
        super().__init__(data)
        self._url = url
        self.headers = {}

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def fake_network(monkeypatch, api, page_tag="v1.2.2", hash_text=None):
    """api: Exception yoki bytes; sahifa -> teg; hash fayli."""

    base = us.ALLOWED_DOWNLOAD_PREFIX

    def request(url, timeout):
        if url == us.LATEST_RELEASE_URL:
            if isinstance(api, Exception):
                raise api
            return Resp(api)
        if url == us.LATEST_PAGE_URL:
            if page_tag is None:
                raise urllib.error.URLError(socket.gaierror("no dns"))
            return Resp(b"<html>", url=f"https://github.com/o/r/releases/tag/{page_tag}")
        if url.endswith(".sha256"):
            if hash_text is None:
                raise http_error(404)
            return Resp(hash_text.encode())
        raise AssertionError(f"kutilmagan URL: {url}")

    monkeypatch.setattr(us, "_request", request)
    monkeypatch.setattr(us.time, "sleep", lambda s: None)
    return base


def test_falls_back_to_github_com_when_api_is_blocked(monkeypatch):
    fake_network(monkeypatch, api=urllib.error.URLError(socket.gaierror("blocked")),
                 hash_text=f"{SHA}  VMPOS-Setup-1.2.2.exe\n")

    info = us.check_for_update("1.2.0")

    assert info.version == "1.2.2" and info.sha256 == SHA
    assert info.installer_name == "VMPOS-Setup-1.2.2.exe"
    assert us.is_allowed_download_url(info.installer_url)
    assert info.installer_url.endswith("/v1.2.2/VMPOS-Setup-1.2.2.exe")


def test_fallback_reports_no_update_when_tag_is_not_newer(monkeypatch):
    fake_network(monkeypatch, api=http_error(403, X_RateLimit_Remaining="0"),
                 page_tag="v1.2.0", hash_text=SHA)

    assert us.check_for_update("1.2.0") is None


def test_fallback_ignores_old_style_releases_without_sha_file(monkeypatch):
    fake_network(monkeypatch, api=http_error(403), page_tag="v1.1.3", hash_text=None)

    assert us.check_for_update("1.0.0") is None          # xato emas, shunchaki yo'q


def test_both_paths_failing_raises_clear_error_with_both_technical_lines(monkeypatch):
    fake_network(monkeypatch, api=urllib.error.URLError(socket.gaierror("api blocked")), page_tag=None)

    with pytest.raises(UpdateError) as caught:
        us.check_for_update("1.2.0")

    error = caught.value
    assert "tekshirib bo'lmadi" in str(error) and "DNS" in str(error)
    assert "GitHub API" in error.technical and "github.com" in error.technical
    assert error.technical.count("URLError") == 2


def test_api_success_does_not_touch_the_fallback(monkeypatch):
    import json

    release = {
        "tag_name": "v1.2.2", "draft": False, "prerelease": False, "body": "yangi",
        "assets": [{
            "name": "VMPOS-Setup-1.2.2.exe", "size": 5, "digest": f"sha256:{SHA}",
            "browser_download_url": us.ALLOWED_DOWNLOAD_PREFIX + "v1.2.2/VMPOS-Setup-1.2.2.exe",
        }],
    }
    seen = []

    def request(url, timeout):
        seen.append(url)
        return Resp(json.dumps(release).encode())

    monkeypatch.setattr(us, "_request", request)

    info = us.check_for_update("1.2.0")

    assert info.version == "1.2.2" and info.notes == "yangi"
    assert seen == [us.LATEST_RELEASE_URL]


# ---------------- qayta urinish ----------------

def test_transient_timeout_is_retried_once(monkeypatch):
    calls = []

    def request(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise TimeoutError("timed out")
        return Resp(b"ok")

    monkeypatch.setattr(us, "_request", request)
    monkeypatch.setattr(us.time, "sleep", lambda s: None)

    with us._open("https://x", 5) as response:
        assert response.read() == b"ok"
    assert len(calls) == 2


def test_http_errors_are_not_retried_and_second_timeout_raises(monkeypatch):
    calls = []
    monkeypatch.setattr(us.time, "sleep", lambda s: None)

    def forbidden(url, timeout):
        calls.append(1)
        raise http_error(403)

    monkeypatch.setattr(us, "_request", forbidden)
    with pytest.raises(urllib.error.HTTPError):
        us._open("https://x", 5)
    assert len(calls) == 1

    calls.clear()

    def slow(url, timeout):
        calls.append(1)
        raise TimeoutError("timed out")

    monkeypatch.setattr(us, "_request", slow)
    with pytest.raises(TimeoutError):
        us._open("https://x", 5)
    assert len(calls) == 2


# ---------------- fayldan o'rnatish ----------------

def make_files(tmp_path, version="1.2.2", payload=PAYLOAD, sha=None, with_sha=True):
    installer = tmp_path / f"VMPOS-Setup-{version}.exe"
    installer.write_bytes(payload)

    if with_sha:
        digest = sha if sha is not None else hashlib.sha256(payload).hexdigest()
        (tmp_path / f"{installer.name}.sha256").write_text(f"{digest}  {installer.name}\n")

    return installer


def test_local_installer_is_verified_and_described(tmp_path):
    info = us.verify_local_installer(make_files(tmp_path), "1.2.0")

    assert info.version == "1.2.2" and info.sha256 == SHA
    assert info.installer_url.endswith("VMPOS-Setup-1.2.2.exe") and info.size == len(PAYLOAD)


def test_local_installer_rejections(tmp_path):
    with pytest.raises(UpdateError, match="nomi"):
        bad = tmp_path / "setup.exe"; bad.write_bytes(b"x")
        us.verify_local_installer(bad, "1.2.0")

    d1 = tmp_path / "a"; d1.mkdir()
    with pytest.raises(UpdateError, match="yangi emas"):
        us.verify_local_installer(make_files(d1, version="1.2.0"), "1.2.0")   # bir xil
    d2 = tmp_path / "b"; d2.mkdir()
    with pytest.raises(UpdateError, match="yangi emas"):
        us.verify_local_installer(make_files(d2, version="1.1.0"), "1.2.0")   # eski

    d3 = tmp_path / "c"; d3.mkdir()
    with pytest.raises(UpdateError, match=".sha256"):
        us.verify_local_installer(make_files(d3, with_sha=False), "1.2.0")

    d4 = tmp_path / "d"; d4.mkdir()
    with pytest.raises(UpdateError, match="SHA-256 mos kelmadi"):
        us.verify_local_installer(make_files(d4, sha="0" * 64), "1.2.0")

    d5 = tmp_path / "e"; d5.mkdir()
    installer = make_files(d5, with_sha=False)
    (d5 / f"{installer.name}.sha256").write_text("hech narsa emas")
    with pytest.raises(UpdateError, match="SHA-256 topilmadi"):
        us.verify_local_installer(installer, "1.2.0")


def test_tampered_local_installer_is_rejected(tmp_path):
    installer = make_files(tmp_path)
    installer.write_bytes(PAYLOAD + b"virus")         # sha eskicha qoldi

    with pytest.raises(UpdateError, match="buzilgan"):
        us.verify_local_installer(installer, "1.2.0")
