"""Fiskalizatsiya uchun umumiy maydonlar (chek va qaytarish).

Hozircha FAQAT saqlash: hech narsa soliq operatoriga yuborilmaydi
(fiscal_mode = "off"). Maydonlar provayder aniqlangach to'ldiriladi,
shuning uchun nomlar provayderga bog'liq emas.
"""

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declared_attr

# Fiskal holat.
FISCAL_NONE = "none"        # fiskallashtirilmagan (yoki fiskalizatsiya o'chiq)
FISCAL_PENDING = "pending"  # yuborilishi kutilmoqda (navbatda)
FISCAL_SENT = "sent"        # operator qabul qildi
FISCAL_FAILED = "failed"    # xato (fiscal_error'da sabab)

FISCAL_STATUSES = (FISCAL_NONE, FISCAL_PENDING, FISCAL_SENT, FISCAL_FAILED)


class FiscalFieldsMixin:
    @declared_attr
    def vat_total(cls):
        # Chek (yoki qaytarish) bo'yicha QQS jami = qatorlar QQS yig'indisi.
        return Column(Float, default=0, nullable=False)

    @declared_attr
    def fiscal_status(cls):
        return Column(String(20), default=FISCAL_NONE, nullable=False)

    @declared_attr
    def fiscal_receipt_id(cls):
        # Operator bergan chek identifikatori.
        return Column(String(64))

    @declared_attr
    def fiscal_sign(cls):
        # Fiskal belgi / imzo (operator bergan).
        return Column(String(255))

    @declared_attr
    def fiscal_qr_url(cls):
        # Chekni tekshirish havolasi (QR-kod shu manzilni kodlaydi).
        return Column(String(512))

    @declared_attr
    def fiscal_at(cls):
        return Column(DateTime)

    @declared_attr
    def fiscal_error(cls):
        return Column(Text)

    @declared_attr
    def fiscal_attempts(cls):
        return Column(Integer, default=0, nullable=False)
