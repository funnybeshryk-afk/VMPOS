"""Chekni rasmga chizish va chop etish (termoprinter yoki PDF).

Chek termoprinterning haqiqiy nuqtalariga mos rasm sifatida chiziladi
(203 dpi: 58 mm qog'ozda 384 nuqta, 80 mm da 576), so'ng printer
drayveri (Windows'dagi o'rnatilgan printer) orqali chop etiladi —
shuning uchun har qanday o'rnatilgan printer ishlaydi (ESC/POS
buyruqlarini qo'lda yuborish kerak emas). Qog'ozni kesish — drayver
sozlamasi.
"""

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPen,
)
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

from app.utils.label_printing import paint_barcode
from app.utils.receipt import BARCODE, GAP, PAIR, RULE

DPI = 203

# paper_mm -> (qog'oz kengligi mm, bosiladigan nuqtalar)
PAPERS = {
    "58": (58, 384),
    "80": (80, 576),
}

_FONT_PX = {"s": 19, "m": 22, "l": 30}
_SIDE_MARGIN = 4
_PAIR_GAP = 12
_RULE_HEIGHT = 14
_GAP_HEIGHT = 14
_BARCODE_HEIGHT = 96
_LINE_PADDING = 4
_FEED_MM = 8        # chek oxirida qog'oz tortish (kesish uchun joy)


class ReceiptPrintError(Exception):
    """Chop etib bo'lmadi (printer yo'q, ochilmadi...). Foydalanuvchiga
    ko'rsatish mumkin; savdoning o'ziga ta'sir qilmaydi."""


def printable_dots(paper_mm):
    return PAPERS[str(paper_mm)][1]


def _font(size, bold):
    font = QFont("Arial")
    font.setPixelSize(_FONT_PX[size])
    font.setBold(bold)

    return font


def _align_flag(align):
    return {
        "center": Qt.AlignHCenter,
        "right": Qt.AlignRight,
    }.get(align, Qt.AlignLeft)


def _measure(line, width):
    """Qator balandligi (px)."""

    if line.kind == RULE:
        return _RULE_HEIGHT

    if line.kind == GAP:
        return _GAP_HEIGHT

    if line.kind == BARCODE:
        return _BARCODE_HEIGHT

    metrics = QFontMetrics(_font(line.size, line.bold))

    if line.kind == PAIR:
        right_width = metrics.horizontalAdvance(line.right)
        left_width = max(40, width - right_width - _PAIR_GAP)
        flags = Qt.TextWordWrap | Qt.AlignLeft
        rect = metrics.boundingRect(0, 0, left_width, 10_000, flags, line.text)

        return max(rect.height(), metrics.height()) + _LINE_PADDING

    flags = Qt.TextWordWrap | _align_flag(line.align)
    rect = metrics.boundingRect(0, 0, width, 10_000, flags, line.text)

    return max(rect.height(), metrics.height()) + _LINE_PADDING


def render_receipt(receipt, paper_mm="80", antialias=True):
    """Chekni QImage'ga chizadi. antialias=False — termoprinter uchun
    (aniq 1-bitli chiziqlar), True — ekrandagi ko'rinish uchun."""

    dots = printable_dots(paper_mm)
    content_width = dots - 2 * _SIDE_MARGIN

    heights = [_measure(line, content_width) for line in receipt.lines]
    total_height = sum(heights) + 2 * _LINE_PADDING

    image = QImage(dots, total_height, QImage.Format_RGB32)
    image.fill(QColor("white"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.TextAntialiasing, antialias)
    painter.setRenderHint(QPainter.Antialiasing, antialias)
    painter.setPen(Qt.black)

    y = _LINE_PADDING

    for line, height in zip(receipt.lines, heights):
        _draw_line(painter, line, y, height, content_width)
        y += height

    painter.end()

    return image


def _draw_line(painter, line, y, height, width):
    x = _SIDE_MARGIN

    if line.kind == RULE:
        painter.save()
        pen = QPen(Qt.black, 1, Qt.DashLine)
        painter.setPen(pen)
        middle = y + height / 2
        painter.drawLine(x, middle, x + width, middle)
        painter.restore()
        return

    if line.kind == GAP:
        return

    if line.kind == BARCODE:
        barcode_width = width * 0.8
        rect = QRectF(x + (width - barcode_width) / 2, y, barcode_width, height)
        paint_barcode(painter, rect, line.text)
        return

    painter.setFont(_font(line.size, line.bold))
    metrics = QFontMetrics(painter.font())

    if line.kind == PAIR:
        right_width = metrics.horizontalAdvance(line.right)
        left_rect = QRectF(x, y, width - right_width - _PAIR_GAP, height)
        painter.drawText(left_rect, Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, line.text)
        right_rect = QRectF(x + width - right_width, y, right_width, height)
        painter.drawText(right_rect, Qt.AlignRight | Qt.AlignTop, line.right)
        return

    rect = QRectF(x, y, width, height)
    painter.drawText(rect, Qt.TextWordWrap | _align_flag(line.align) | Qt.AlignTop, line.text)


def available_printers():
    return QPrinterInfo.availablePrinterNames()


def default_printer_name():
    return QPrinterInfo.defaultPrinterName()


def print_image(image, paper_mm="80", printer_name="", pdf_path=None):
    """Chek rasmini chop etadi. pdf_path berilsa — PDF fayl (printersiz,
    sinash va saqlash uchun). Muvaffaqiyatsizlikda ReceiptPrintError."""

    paper, dots = PAPERS[str(paper_mm)]
    printer = QPrinter(QPrinter.HighResolution)

    if pdf_path:
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(pdf_path))
    else:
        names = available_printers()

        if printer_name:
            if printer_name not in names:
                raise ReceiptPrintError(
                    f"Printer topilmadi: {printer_name}. Sozlamalarda "
                    "printerni qayta tanlang."
                )
            printer.setPrinterName(printer_name)
        elif not names:
            raise ReceiptPrintError(
                "Kompyuterda printer o'rnatilmagan. Printerni ulang va "
                "Sozlamalarda tanlang."
            )

    height_mm = image.height() / DPI * 25.4 + _FEED_MM

    printer.setPageSize(QPageSize(QSizeF(paper, height_mm), QPageSize.Millimeter))
    printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)
    printer.setFullPage(True)

    painter = QPainter()

    if not painter.begin(printer):
        raise ReceiptPrintError(
            "Printerni ochib bo'lmadi. Printer yoqilgan va ulanganini "
            "tekshiring."
        )

    try:
        page = QRectF(printer.pageRect(QPrinter.DevicePixel))
        printable_mm = dots / DPI * 25.4
        target_width = page.width() * (printable_mm / paper)
        scale = target_width / image.width()
        target_height = image.height() * scale
        x = (page.width() - target_width) / 2

        painter.drawImage(QRectF(x, 0, target_width, target_height), image)
    finally:
        painter.end()
