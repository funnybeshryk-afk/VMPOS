"""Chek (kvitansiya) mazmuni — UI va printerdan MUSTAQIL, sof ma'lumot.

build_receipt() chek qatorlari ro'yxatini quradi; chizish va chop etish
alohida (receipt_render.py). Shu sabab mazmun Qt'siz sinaladi.

MUHIM: bu FISKAL chek EMAS. Fiskal rekvizitlar (fiskal belgi, QR) yo'q;
chekda "Fiskal chek emas" yozuvi chiqadi (fiscal_status != "sent" bo'lsa).
"""

from dataclasses import dataclass, field

from app.utils.formatters import format_money, format_quantity

# Qator turlari
TEXT = "text"        # bitta matn (o'ralishi mumkin)
PAIR = "pair"        # chapda matn, o'ngda qiymat
RULE = "rule"        # ajratuvchi chiziq
GAP = "gap"          # bo'sh joy
BARCODE = "barcode"  # Code128

DEFAULT_FOOTER = "Xaridingiz uchun rahmat!"
NON_FISCAL_NOTE = "Fiskal chek emas"

_STATUS_TEXT = {
    "partially_refunded": "Qisman qaytarilgan",
    "refunded": "Qaytarilgan",
}


@dataclass
class ReceiptLine:
    kind: str
    text: str = ""
    right: str = ""
    align: str = "left"      # left | center | right
    bold: bool = False
    size: str = "m"          # s | m | l


@dataclass
class Receipt:
    lines: list = field(default_factory=list)

    def texts(self):
        """Test/diagnostika uchun: barcha matnlar (chap + o'ng)."""

        out = []

        for line in self.lines:
            if line.text:
                out.append(line.text)
            if line.right:
                out.append(line.right)

        return out


def _money(value):
    return f"{format_money(value)} so'm"


def build_receipt(sale, items, store=None, options=None):
    """sale/items — Sale va SaleItem (yoki ular kabi ob'ektlar).

    store: {store_name, store_phone, store_address, store_tin,
            store_legal_name}.
    options: {footer, show_barcode, non_fiscal_note}.
    """

    store = store or {}
    options = options or {}
    lines = []

    def text(value, align="left", bold=False, size="m"):
        lines.append(ReceiptLine(TEXT, value, align=align, bold=bold, size=size))

    def pair(left, right, bold=False, size="m"):
        lines.append(ReceiptLine(PAIR, left, right, bold=bold, size=size))

    def rule():
        lines.append(ReceiptLine(RULE))

    def gap():
        lines.append(ReceiptLine(GAP))

    # ---- sarlavha ------------------------------------------------
    store_name = (store.get("store_name") or "").strip() or "VMPOS"
    text(store_name, "center", bold=True, size="l")

    legal_name = (store.get("store_legal_name") or "").strip()

    if legal_name and legal_name != store_name:
        text(legal_name, "center", size="s")

    for key in ("store_address", "store_phone"):
        value = (store.get(key) or "").strip()

        if value:
            text(value, "center", size="s")

    tin = (store.get("store_tin") or "").strip()

    if tin:
        text(f"STIR: {tin}", "center", size="s")

    rule()

    # ---- chek ma'lumoti -----------------------------------------
    pair("Chek", f"#{sale.id}")
    pair("Sana", sale.created_at.strftime("%d.%m.%Y %H:%M"))

    status_text = _STATUS_TEXT.get(sale.status)

    if status_text:
        text(f"** {status_text} **", "center", bold=True)

    rule()

    # ---- qatorlar --------------------------------------------------
    for item in items:
        text(item.product_name, bold=True)
        pair(
            f"{format_quantity(item.quantity)} × {format_money(item.price)}",
            format_money(item.line_total),
        )

    rule()

    # ---- jami va QQS --------------------------------------------
    pair("JAMI", _money(sale.total_amount), bold=True, size="l")

    vat_by_rate = {}

    for item in items:
        if (item.vat_amount or 0) > 0:
            vat_by_rate[item.vat_rate] = (
                vat_by_rate.get(item.vat_rate, 0) + item.vat_amount
            )

    for rate in sorted(vat_by_rate):
        pair(
            f"shu jumladan QQS {rate:g}%",
            _money(round(vat_by_rate[rate], 2)),
            size="s",
        )

    # ---- to'lov --------------------------------------------------
    method = sale.payment_method

    if method == "cash":
        pair("Naqd (berildi)", _money(sale.paid_amount))
        pair("Qaytim", _money(sale.change_amount))
    elif method == "card":
        pair("Karta", _money(sale.card_amount or sale.total_amount))
    elif method == "mixed":
        pair("Naqd", _money(sale.cash_amount))
        pair("Karta", _money(sale.card_amount))
    elif method == "debt":
        if sale.cash_amount > 0:
            pair("Naqd", _money(sale.cash_amount))

        debt = sale.total_amount - sale.cash_amount - sale.card_amount
        pair("Nasiya (qarzga)", _money(round(debt, 2)))

    rule()

    # ---- pastki qism -------------------------------------------
    footer = options.get("footer", DEFAULT_FOOTER)

    if footer:
        text(footer, "center")

    if options.get("non_fiscal_note", True) and sale.fiscal_status != "sent":
        text(NON_FISCAL_NOTE, "center", size="s")

    if options.get("show_barcode", True):
        gap()
        lines.append(ReceiptLine(BARCODE, str(sale.id)))

    gap()

    return Receipt(lines)
