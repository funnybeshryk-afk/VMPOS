"""Windows sarlavha (title bar) rangi.

Oyna sarlavhasi tizimniki (oq/kulrang) bo'lib, qora chap rels va qolgan
interfeysdan "uzilib" turardi. DWM orqali sarlavhani rels bilan bir xil
"ink" rangiga bo'yaymiz — rels + sarlavha yagona qora ramka bo'ladi.

Faqat Windows'da va xavfsiz: eski Windows 10 yoki boshqa tizimda atribut
qo'llab-quvvatlanmasa — jimgina o'tkazib yuboriladi (tizim sarlavhasi
qoladi, dastur ishlashiga ta'sir qilmaydi).
"""

import sys

# DWM atributlari (dwmapi.h). Caption/Text/Border rangi — Windows 11 (22000+),
# immersive dark mode — Windows 10 20H1+ (19 — eski nomerlash).
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
_DWMWA_BORDER_COLOR = 34
_DWMWA_CAPTION_COLOR = 35
_DWMWA_TEXT_COLOR = 36

TITLE_BAR_COLOR = "#1c1917"   # ink — chap rels bilan bir xil
TITLE_TEXT_COLOR = "#f6f3ee"  # fon (krem) rangi


def hex_to_colorref(color):
    """"#RRGGBB" -> Windows COLORREF (0x00BBGGRR)."""

    value = color.lstrip("#")

    if len(value) != 6:
        raise ValueError(color)

    red, green, blue = (int(value[i:i + 2], 16) for i in (0, 2, 4))

    return (blue << 16) | (green << 8) | red


def style_title_bar(window, platform=None, dwm_set=None):
    """Oyna sarlavhasini qora qiladi. True — hech bo'lmasa bitta atribut
    qo'llandi. `platform`/`dwm_set` — sinash uchun almashtiriladi."""

    if (platform or sys.platform) != "win32":
        return False

    try:
        hwnd = int(window.winId())
        setter = dwm_set or _dwm_set_attribute
        applied = False

        for attribute, value in (
            (_DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
            (_DWMWA_CAPTION_COLOR, hex_to_colorref(TITLE_BAR_COLOR)),
            (_DWMWA_TEXT_COLOR, hex_to_colorref(TITLE_TEXT_COLOR)),
            (_DWMWA_BORDER_COLOR, hex_to_colorref(TITLE_BAR_COLOR)),
        ):
            applied = bool(setter(hwnd, attribute, value)) or applied

        return applied
    except Exception:
        return False


def _dwm_set_attribute(hwnd, attribute, value):
    import ctypes
    from ctypes import wintypes

    data = ctypes.c_int(value)
    result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(attribute),
        ctypes.byref(data),
        ctypes.sizeof(data),
    )

    return result == 0  # S_OK
