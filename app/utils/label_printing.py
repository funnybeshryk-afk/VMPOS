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

# Yorliqlar A4 varaqqa panjara (grid) tartibida joylashtiriladi —
# yorliq printeri emas, oddiy printerda o'z-yorliq qog'ozida yoki
# PDF sifatida ko'p nusxani bir sahifada chop etish uchun.
SHEET_WIDTH_MM = 210.0
SHEET_HEIGHT_MM = 297.0
SHEET_MARGIN_MM = 5.0
LABEL_GAP_MM = 2.0


def compute_grid_layout(label_width_mm, label_height_mm):
    """Berilgan yorliq o'lchamida A4 varaqqa necha ustun/qator
    sig'ishini hisoblaydi (SHEET_MARGIN_MM chekka, LABEL_GAP_MM
    yorliqlar orasidagi bo'shliq bilan)."""

    usable_width = SHEET_WIDTH_MM - 2 * SHEET_MARGIN_MM
    usable_height = SHEET_HEIGHT_MM - 2 * SHEET_MARGIN_MM

    cols = max(
        1,
        int(
            (usable_width + LABEL_GAP_MM)
            // (label_width_mm + LABEL_GAP_MM)
        ),
    )
    rows = max(
        1,
        int(
            (usable_height + LABEL_GAP_MM)
            // (label_height_mm + LABEL_GAP_MM)
        ),
    )

    return cols, rows


def paginate_entries(entries, cols, rows):
    """Tekis ro'yxatni sahifalarga bo'ladi: [[1-sahifa...], [2-...]].

    Har sahifada eng ko'pi bilan cols*rows dona yorliq bo'ladi —
    Chop etish va PDF ikkalasi ham shu funksiyadan foydalanadi, shu
    sabab ikkalasida ham bir xil sahifalanish bo'ladi.
    """

    per_page = max(1, cols * rows)

    return [
        entries[index:index + per_page]
        for index in range(0, len(entries), per_page)
    ]


def paint_label_sheet(
    painter, sheet_rect, page_entries, cols, label_width_mm, label_height_mm
):
    """Bitta A4 varaqqa (sheet_rect — device/piksel koordinatalarida)
    panjara tartibida bir nechta yorliqni chizadi.

    Preview, Chop etish va PDF eksporti — uchalasi ham shu bitta
    funksiyadan foydalanadi, shuning uchun preview haqiqatda
    chop etiladigan tartibni aynan ko'rsatadi.
    """

    px_per_mm = sheet_rect.width() / SHEET_WIDTH_MM

    margin_px = SHEET_MARGIN_MM * px_per_mm
    gap_px = LABEL_GAP_MM * px_per_mm
    label_w_px = label_width_mm * px_per_mm
    label_h_px = label_height_mm * px_per_mm

    for index, product in enumerate(page_entries):
        row = index // cols
        col = index % cols

        x = sheet_rect.left() + margin_px + col * (label_w_px + gap_px)
        y = sheet_rect.top() + margin_px + row * (label_h_px + gap_px)

        paint_product_label(
            painter, QRectF(x, y, label_w_px, label_h_px), product
        )


def _fit_name_text(name, font, name_rect):
    """Bo'sh joysiz uzun nom (masalan bitta so'z) name_rect'ga
    sig'masa, TextWordWrap yordam bermaydi — Qt so'z ichida
    bo'lmaydi, natijada matn markazlashtirilgan holda ikki
    tomondan kesilib qoladi (masalan "MAHSULOT_NOMI_UZUN" ->
    "SULOT_NOMI_UZ" ko'rinishida). Shu holatni oldini olish uchun
    eng uzun bo'linmas so'z katakchaga sig'maydigan bo'lsa, butun
    matn "..." bilan bo'ktirilib qisqartiriladi.
    """

    if not name:
        return name

    metrics = QFontMetrics(font)
    longest_word = max(name.split(), key=len, default="")

    if metrics.horizontalAdvance(longest_word) <= name_rect.width():
        return name

    return metrics.elidedText(name, Qt.ElideRight, int(name_rect.width()))


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
        _fit_name_text(product.name or "", name_font, name_rect),
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
