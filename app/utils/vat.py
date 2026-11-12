"""QQS (NDS) hisoblash va fiskal kodlarni tekshirish.

Taxmin (tasdiqlash kerak): chakana narxlar QQS'NI O'Z ICHIGA OLADI
(kassa cheki jami summasi narxlar yig'indisiga teng), shuning uchun QQS
summasi "ichidan" ajratiladi:  qqs = summa * stavka / (100 + stavka).
Hisob QATOR bo'yicha va tiyingacha yaxlitlanadi (ROUND_HALF_UP): fiskal
chekda har bir qator o'z QQS summasi bilan keladi, chek jami — qatorlar
yig'indisi.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

VAT_RATE_MAX = 100
CODE_MAX_LENGTH = 20


def _to_decimal(value):
    return Decimal(str(value or 0))


def vat_included(amount, rate):
    """Narx ichidagi QQS summasi (2 xona, ROUND_HALF_UP). stavka 0/None -> 0."""

    rate = _to_decimal(rate)

    if rate <= 0:
        return 0.0

    amount = _to_decimal(amount)
    vat = amount * rate / (Decimal(100) + rate)

    return float(vat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def effective_vat_rate(product_rate, default_rate):
    """Mahsulotning o'z stavkasi bo'lsa — shu, bo'sh (None) bo'lsa —
    do'konning standart stavkasi."""

    if product_rate is None:
        return float(default_rate or 0)

    return float(product_rate)


def validate_vat_rate(value):
    """Stavka (%) — 0..100 oralig'ida son. Bo'sh (None/"") -> None
    ("do'konning standart stavkasi")."""

    if value is None or str(value).strip() == "":
        return None

    try:
        rate = float(str(value).replace(" ", "").replace(",", "."))
    except ValueError:
        raise ValueError("QQS stavkasi son bo'lishi kerak.")

    if not 0 <= rate <= VAT_RATE_MAX:
        raise ValueError("QQS stavkasi 0 dan 100 gacha bo'lishi kerak.")

    return rate


def validate_digits_code(value, label):
    """IKPU / qadoq kodi: bo'sh yoki faqat raqamlar (probellar olib
    tashlanadi). Aniq uzunlik ATAYLAB tekshirilmaydi — soliq qo'mitasi
    talabi o'zgarishi mumkin; faqat shakl (raqamlar) va maksimal uzunlik."""

    code = re.sub(r"\s+", "", str(value or ""))

    if code == "":
        return ""

    if not code.isdigit():
        raise ValueError(f"{label} faqat raqamlardan iborat bo'lishi kerak.")

    if len(code) > CODE_MAX_LENGTH:
        raise ValueError(
            f"{label} {CODE_MAX_LENGTH} belgidan oshmasligi kerak."
        )

    return code


def validate_ikpu(value):
    return validate_digits_code(value, "IKPU kodi")


def validate_package_code(value):
    return validate_digits_code(value, "Qadoq kodi")


def validate_tin(value):
    """STIR (INN): bo'sh yoki faqat raqamlar (yuridik shaxs — 9, yakka
    tartibdagi tadbirkor/JSHSHIR — 14 xona bo'lishi mumkin)."""

    code = re.sub(r"\s+", "", str(value or ""))

    if code == "":
        return ""

    if not code.isdigit() or len(code) > 14:
        raise ValueError("STIR faqat raqamlardan iborat (9 yoki 14 xona).")

    return code
