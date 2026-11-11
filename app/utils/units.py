"""O'lchov birliklari bilan bog'liq umumiy qoidalar."""

# Bu birliklarda miqdor butun emas (kg) — og'irlik dialogi bilan
# kiritiladi, "+/-" qadami mazmunsiz.
_WEIGHT_UNITS = {"kg", "кг"}


def is_weight_unit(unit):
    return (unit or "").strip().lower() in _WEIGHT_UNITS
