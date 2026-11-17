import pytest

from app.utils import win_chrome


def test_hex_to_colorref_is_bgr():
    assert win_chrome.hex_to_colorref("#1c1917") == 0x17191C
    assert win_chrome.hex_to_colorref("#ff0000") == 0x0000FF
    assert win_chrome.hex_to_colorref("#0000ff") == 0xFF0000

    with pytest.raises(ValueError):
        win_chrome.hex_to_colorref("#abc")


def test_noop_outside_windows():
    called = []

    assert win_chrome.style_title_bar(
        object(), platform="linux", dwm_set=lambda *a: called.append(a)
    ) is False
    assert called == []


def test_applies_dark_mode_and_colors_on_windows():
    class Window:
        def winId(self):
            return 1234

    calls = []

    ok = win_chrome.style_title_bar(
        Window(), platform="win32",
        dwm_set=lambda hwnd, attr, value: calls.append((hwnd, attr, value)) or True,
    )

    assert ok is True
    attrs = {attr: value for _hwnd, attr, value in calls}
    assert all(hwnd == 1234 for hwnd, _a, _v in calls)
    assert attrs[20] == 1                                   # dark mode
    assert attrs[35] == win_chrome.hex_to_colorref("#1c1917")  # caption
    assert attrs[36] == win_chrome.hex_to_colorref("#f6f3ee")  # text


def test_failure_never_breaks_the_window():
    class Window:
        def winId(self):
            raise RuntimeError("no hwnd")

    assert win_chrome.style_title_bar(Window(), platform="win32") is False
    assert win_chrome.style_title_bar(
        type("W", (), {"winId": lambda self: 1})(),
        platform="win32",
        dwm_set=lambda *a: (_ for _ in ()).throw(OSError("old windows")),
    ) is False
