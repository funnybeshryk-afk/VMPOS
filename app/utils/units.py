"""O'lchov birliklari bilan bog'liq umumiy qoidalar."""

# Bu birliklarda miqdor butun emas (kg) — og'irlik dialogi bilan
# kiritiladi, "+/-" qadami mazmunsiz.
_WEIGHT_UNITS = {"kg", "кг"}

# Rus tilida mashhur o'zbekcha birliklar qisqartmasi. Birlik —
# foydalanuvchi kiritgan matn, shuning uchun noma'lumi o'zgarishsiz qoladi.
_RU_UNITS = {
    "dona": "шт",
    "ta": "шт",
    "kg": "кг",
    "litr": "л",
    "l": "л",
    "metr": "м",
    "m": "м",
    "gr": "г",
    "g": "г",
    "gramm": "г",
    "paket": "уп.",
    "qadoq": "уп.",
    "quti": "кор.",
}


def unit_label(unit):
    """Birlikni joriy interfeys tilida ko'rsatish uchun."""

    from app.i18n import get_language

    text = (unit or "").strip()

    if get_language() == "ru":
        return _RU_UNITS.get(text.lower(), text)

    return text


def is_weight_unit(unit):
    return (unit or "").strip().lower() in _WEIGHT_UNITS
