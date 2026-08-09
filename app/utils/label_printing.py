from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QPainterPath

from app.utils.barcode_render import get_barcode_modules
from app.utils.formatters import format_money

_PADDING_RATIO = 0.06

LABEL_SIZE_PRESETS = {
    "40 x 30 mm": (40.0, 30.0),
    "58 x 40 mm": (58.0, 40.0),
    "58 x 30 mm": (58.0, 30.0),
    "30 x 20 mm": (30.0, 20.0),
}


def paint_product_label(painter, rect, product):
    """Bitta narx yorlig'i — nomi, narxi, shtrix-kod.

    Preview'da ham (ekrandagi QPixmap), chop etishda ham (QPrinter)
    aynan shu funksiya ishlatiladi — ikkalasi bir xil ko'rinishini
    kafolatlaydi, DPI/o'lchamdan qat'iy nazar (barcha o'lchamlar
    `rect`ga nisbatan foiz sifatida hisoblanadi).
    """

    painter.save()

    padding = rect.width() * _PADDING_RATIO
    content_rect = rect.adjusted(
        padding, padding, -padding, -padding
    )

    painter.setPen(Qt.black)
    painter.drawRect(rect.adjusted(0, 0, -1, -1))

    name_rect = QRectF(
        content_rect.left(),
        content_rect.top(),
        content_rect.width(),
        content_rect.height() * 0.34,
    )
    name_font = QFont("Arial")
    name_font.setPixelSize(max(8, int(content_rect.height() * 0.13)))
    name_font.setBold(True)
    painter.setFont(name_font)
    painter.drawText(
        name_rect,
        Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignTop,
        product.name or "",
    )

    price_rect = QRectF(
        content_rect.left(),
        name_rect.bottom(),
        content_rect.width(),
        content_rect.height() * 0.26,
    )
    price_font = QFont("Arial")
    price_font.setPixelSize(max(10, int(content_rect.height() * 0.19)))
    price_font.setBold(True)
    painter.setFont(price_font)
    painter.drawText(
        price_rect,
        Qt.AlignHCenter | Qt.AlignVCenter,
        f"{format_money(product.sell_price)} so'm",
    )

    barcode_rect = QRectF(
        content_rect.left(),
        price_rect.bottom(),
        content_rect.width(),
        content_rect.bottom() - price_rect.bottom(),
    )
    _paint_barcode(painter, barcode_rect, product.barcode)

    painter.restore()


def _paint_barcode(painter, rect, code):
    """Code128 chiziqlarini to'g'ridan-to'g'ri to'rtburchaklar bilan
    chizadi — nima uchun oraliq SVG formatidan foydalanilmasligi
    barcode_render.get_barcode_modules() docstring'ida tushuntirilgan.
    """

    modules = get_barcode_modules(code)

    if not modules:
        return

    text_height = rect.height() * 0.22

    # Tinch zona (quiet zone) — chiziqlarning ikkala yonida bo'sh
    # joy, skanerlar barcode boshi/oxirini shu orqali aniqlaydi.
    # .build() faqat xom modul ketma-ketligini beradi (yozuvchisiz
    # chaqirilgani uchun), shuning uchun bu yerda o'zimiz qo'shamiz.
    quiet_zone = rect.width() * 0.05
    bars_rect = QRectF(
        rect.left() + quiet_zone,
        rect.top(),
        rect.width() - 2 * quiet_zone,
        rect.height() - text_height,
    )
    module_width = bars_rect.width() / len(modules)

    # Antialiasing qo'shni modullar orasida noaniq, oq "tirqish"
    # chiziqlarni hosil qilishi mumkin (har bir to'rtburchak alohida
    # silliqlanadi) — shtrix-kod uchun bu chiziqlar skanerni
    # chalg'itishi mumkin, shuning uchun bu yerda o'chirilgan va
    # yagona QPainterPath orqali bir martada to'ldiriladi.
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, False)

    path = QPainterPath()
    x = bars_rect.left()

    for bit in modules:
        if bit == "1":
            path.addRect(
                QRectF(x, bars_rect.top(), module_width, bars_rect.height())
            )
        x += module_width

    painter.fillPath(path, Qt.black)
    painter.restore()

    text_rect = QRectF(
        rect.left(), bars_rect.bottom(), rect.width(), text_height
    )
    text_font = QFont("Arial")
    text_font.setPixelSize(max(6, int(text_height * 0.7)))

    metrics = QFontMetrics(text_font)
    elided = metrics.elidedText(
        code, Qt.ElideRight, int(text_rect.width())
    )

    painter.save()
    painter.setFont(text_font)
    painter.setPen(Qt.black)
    painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignVCenter, elided)
    painter.restore()


def build_label_entries(products_with_copies):
    """[(product, copies), ...] -> [product, product, ...] tekis
    ro'yxat, chop etishda har bir nusxa bitta sahifa bo'ladi."""

    entries = []

    for product, copies in products_with_copies:
        entries.extend([product] * max(0, int(copies)))

    return entries
