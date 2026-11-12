import hashlib
import io

import pytest

from app.services import update_service as us
from app.services.update_service import UpdateError, UpdateInfo

BASE = us.ALLOWED_DOWNLOAD_PREFIX + "v1.1.0/"
PAYLOAD = b"fake-installer-bytes" * 1000
GOOD_SHA = hashlib.sha256(PAYLOAD).hexdigest()


def release(**override):
    data = {
        "tag_name": "v1.1.0",
        "draft": False,
        "prerelease": False,
        "body": "Yangi imkoniyatlar",
        "assets": [{
            "name": "VMPOS-Setup-1.1.0.exe",
            "browser_download_url": BASE + "VMPOS-Setup-1.1.0.exe",
            "size": len(PAYLOAD),
            "digest": "sha256:" + GOOD_SHA,
        }],
    }
    data.update(override)
    return data


@pytest.mark.parametrize("remote,current,expected", [
    ("v1.1.0", "1.0.0", True),
    ("v1.0.1", "1.0.0", True),
    ("v1.10.0", "1.9.0", True),     # son bo'yicha, matn bo'yicha emas
    ("v1.0.0", "1.0.0", False),
    ("v1.0", "1.0.0", False),       # (1,0) == (1,0,0)
    ("v0.9.9", "1.0.0", False),
    ("beta", "1.0.0", False),
    ("v1.2.x", "1.0.0", False),
    ("", "1.0.0", False),
])
def test_is_newer(remote, current, expected):
    assert us.is_newer(remote, current) is expected


def test_valid_release_is_parsed():
    info = us.parse_release(release(), "1.0.0")

    assert info.version == "1.1.0"
    assert info.installer_name == "VMPOS-Setup-1.1.0.exe"
    assert info.sha256 == GOOD_SHA


def test_no_update_when_not_newer_or_draft_or_prerelease():
    assert us.parse_release(release(tag_name="v1.0.0"), "1.0.0") is None
    assert us.parse_release(release(draft=True), "1.0.0") is None
    assert us.parse_release(release(prerelease=True), "1.0.0") is None


def test_release_without_checksum_is_ignored():
    r = release()
    del r["assets"][0]["digest"]

    assert us.parse_release(r, "1.0.0") is None


def test_release_with_foreign_download_url_is_ignored():
    r = release()
    r["assets"][0]["browser_download_url"] = "https://evil.example/VMPOS-Setup-1.1.0.exe"

    assert us.parse_release(r, "1.0.0") is None


def test_release_with_unexpected_asset_name_is_ignored():
    r = release()
    r["assets"][0]["name"] = "malware.exe"
    r["assets"][0]["browser_download_url"] = BASE + "malware.exe"

    assert us.parse_release(r, "1.0.0") is None


def test_checksum_can_come_from_sha256_asset(monkeypatch):
    r = release()
    del r["assets"][0]["digest"]
    r["assets"].append({
        "name": "VMPOS-Setup-1.1.0.exe.sha256",
        "browser_download_url": BASE + "VMPOS-Setup-1.1.0.exe.sha256",
    })
    monkeypatch.setattr(
        us, "_request",
        lambda url, timeout: FakeResponse(f"{GOOD_SHA}  VMPOS-Setup-1.1.0.exe\n".encode()),
    )

    assert us.parse_release(r, "1.0.0").sha256 == GOOD_SHA


class FakeResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def info(sha=GOOD_SHA, url=BASE + "VMPOS-Setup-1.1.0.exe"):
    return UpdateInfo("1.1.0", "", "VMPOS-Setup-1.1.0.exe", url, sha, len(PAYLOAD))


def test_download_verifies_and_reports_progress(monkeypatch):
    monkeypatch.setattr(us, "_request", lambda url, timeout: FakeResponse(PAYLOAD))
    seen = []

    path = us.download_installer(info(), progress=lambda a, b: seen.append((a, b)))

    assert path.read_bytes() == PAYLOAD
    assert seen[-1] == (len(PAYLOAD), len(PAYLOAD))


def test_download_with_wrong_hash_is_rejected_and_deleted(monkeypatch):
    monkeypatch.setattr(us, "_request", lambda url, timeout: FakeResponse(PAYLOAD + b"tampered"))
    created = []
    real_mkdtemp = us.tempfile.mkdtemp
    monkeypatch.setattr(us.tempfile, "mkdtemp", lambda **kw: created.append(real_mkdtemp(**kw)) or created[-1])

    with pytest.raises(UpdateError, match="SHA-256"):
        us.download_installer(info())

    import os
    assert not os.path.exists(created[0])


def test_download_refuses_foreign_url(monkeypatch):
    monkeypatch.setattr(us, "_request", lambda url, timeout: pytest.fail("tarmoqqa chiqmasligi kerak"))

    with pytest.raises(UpdateError):
        us.download_installer(info(url="https://evil.example/x.exe"))


def test_download_can_be_cancelled(monkeypatch):
    monkeypatch.setattr(us, "_request", lambda url, timeout: FakeResponse(PAYLOAD))

    with pytest.raises(us.UpdateCancelled):
        us.download_installer(info(), is_cancelled=lambda: True)


def test_installer_is_never_launched_outside_frozen_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(us.subprocess, "Popen", lambda *a, **k: pytest.fail("ishga tushmasligi kerak"))

    with pytest.raises(UpdateError):
        us.launch_installer(tmp_path / "x.exe")


def test_download_url_check_ignores_repo_name_case_but_not_host_or_path():
    ok = "https://github.com/funnybeshryk-afk/vmpos/releases/download/v1/x.exe"
    assert us.is_allowed_download_url(ok)
    assert us.is_allowed_download_url(ok.replace("vmpos", "VMPOS"))
    assert not us.is_allowed_download_url("https://github.com.evil.example/funnybeshryk-afk/vmpos/releases/download/v1/x.exe")
    assert not us.is_allowed_download_url("http://github.com/funnybeshryk-afk/vmpos/releases/download/v1/x.exe")
    assert not us.is_allowed_download_url("https://github.com/other/repo/releases/download/v1/x.exe")
    assert not us.is_allowed_download_url(None)
