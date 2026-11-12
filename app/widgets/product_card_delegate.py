from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

from app.utils.category_icons import icon_for_category
from app.utils.formatters import format_money, format_quantity
from app.utils.icons import load_icon
from app.utils.paths import resolve_data_path
from app.utils.units import is_weight_unit
from app.widgets.badge import resolve_stock_status
from app.widgets.product_list_model import CartQtyRole, ProductRole

CARD_SIZE = QSize(244, 322)

_CARD_MARGIN = 6
_CARD_RADIUS = 22
_PADDING = 14
_PHOTO_HEIGHT = 150
_PHOTO_RADIUS = 16
_PLACEHOLDER_ICON_SIZE = 48
_ADD_BUTTON_SIZE = 52

# QListView virtuallashtirilgan bo'lishi uchun kartochka setIndexWidget()
# orqali haqiqiy QWidget bilan emas, shu delegate ichida QPainter bilan
# qo'lda chiziladi — shuning uchun QSS bu yerga yetib bormaydi. Ranglar
# style.qss palitrasidagi qiymatlar bilan qo'lda muvofiqlashtirilgan
# (bitta manba emas, lekin muqobili yo'q).
_COLOR_CARD_BG = QColor("#ffffff")
_COLOR_CARD_BORDER = QColor("#ece7df")
_COLOR_CARD_BORDER_HOVER = QColor("#a8a29e")
_COLOR_ACCENT = QColor("#059669")
_COLOR_PHOTO_BG = QColor("#f6f3ee")
_COLOR_INK = QColor("#1c1917")
_COLOR_NAME = QColor("#1c1917")
_COLOR_PRICE = QColor("#047857")
_COLOR_MUTED = QColor("#78716c")
_COLOR_ON_DARK = QColor("#ffffff")
_COLOR_PLACEHOLDER_ICON = "#a8a29e"

_BADGE_COLORS = {
    "success": (QColor("#d1fae5"), QColor("#065f46")),
    "warning": (QColor("#fef3c7"), QColor("#92400e")),
    "danger": (QColor("#fee2e2"), QColor("#991b1b")),
    "neutral": (QColor("#f3efe8"), QColor("#292524")),
}


class ProductCardDelegate(QStyledItemDelegate):
    """Katalog kartochkasini qo'lda chizadigan delegate.

    Foto/ikonka pixmaplari keshlanadi (self._photo_cache/_icon_cache)
    — aks holda har bir paint() chaqiruvida (masalan skroll paytida)
    diskdan qayta o'qish yoki SVG'ni qayta render qilish kerak
    bo'lardi, bu virtualizatsiyaning o'zini sekinlashtirib qo'yardi.

    Korzinadagi mahsulot izumrud ramka va fotosuratdagi "2 ta"
    belgisi bilan ajratiladi (CartQtyRole). Kartochkaning istalgan
    joyini bosish 1 ta qo'shadi; "+" shunchaki shu harakatning
    ko'rinadigan belgisi.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._photo_cache = {}
        self._icon_cache = {}

    def sizeHint(self, option, index):
        # Kenglik ProductGrid._fit_columns() bergan katak kengligi
        # (gridSize) bilan belgilanadi; bu yerda faqat boshlang'ich.
        return CARD_SIZE

    def paint(self, painter, option, index):
        product = index.data(ProductRole)

        if product is None:
            return

        in_cart = index.data(CartQtyRole) or 0

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        card_rect = option.rect.adjusted(
            _CARD_MARGIN, _CARD_MARGIN, -_CARD_MARGIN, -_CARD_MARGIN
        )
        is_hovered = bool(option.state & QStyle.State_MouseOver)

        if in_cart:
            border_pen = QPen(_COLOR_ACCENT, 2)
        elif is_hovered:
            border_pen = QPen(_COLOR_CARD_BORDER_HOVER, 1)
        else:
            border_pen = QPen(_COLOR_CARD_BORDER, 1)

        painter.setPen(border_pen)
        painter.setBrush(_COLOR_CARD_BG)
        # Ramka qalinligi (2 px) kartochka chegarasidan chiqib ketmasligi
        # uchun yarim piksel ichkariga suriladi.
        painter.drawRoundedRect(
            QRectF(card_rect).adjusted(0.5, 0.5, -0.5, -0.5),
            _CARD_RADIUS,
            _CARD_RADIUS,
        )

        content_rect = card_rect.adjusted(
            _PADDING, _PADDING, -_PADDING, -_PADDING
        )

        photo_rect = QRect(
            content_rect.left(),
            content_rect.top(),
            content_rect.width(),
            _PHOTO_HEIGHT,
        )
        self._paint_photo(painter, product, photo_rect)
        self._paint_badge(painter, product, photo_rect)

        if in_cart:
            self._paint_cart_marker(painter, product, in_cart, photo_rect)

        self._paint_text(painter, option, product, content_rect, photo_rect)
        self._paint_add_button(painter, content_rect)

        painter.restore()

    def _paint_photo(self, painter, product, photo_rect):
        painter.setPen(Qt.NoPen)
        painter.setBrush(_COLOR_PHOTO_BG)
        painter.drawRoundedRect(photo_rect, _PHOTO_RADIUS, _PHOTO_RADIUS)

        pixmap = self._resolve_pixmap(product, photo_rect.size())

        pixmap_rect = pixmap.rect()
        pixmap_rect.moveCenter(photo_rect.center())

        painter.setClipRect(photo_rect)
        painter.drawPixmap(pixmap_rect.topLeft(), pixmap)
        painter.setClipping(False)

    def _resolve_pixmap(self, product, target_size):
        image_file = resolve_data_path(product.image_path)

        if image_file is not None and image_file.is_file():
            cache_key = (
                "photo",
                product.image_path,
                target_size.width(),
                target_size.height(),
            )
            cached = self._photo_cache.get(cache_key)

            if cached is not None:
                return cached

            candidate = QPixmap(str(image_file))

            if not candidate.isNull():
                # KeepAspectRatioByExpanding to'ldirib, chetlarini
                # kesib tashlar edi (masalan tarvuz surati tepa-
                # pastdan kesilib qolardi). KeepAspectRatio esa
                # to'liq sig'diradi — natijada rasm atrofida ozgina
                # bo'sh joy qolishi mumkin, lekin hech narsa
                # kesilmaydi, bu kesilgan suratdan yaxshiroq.
                scaled = candidate.scaled(
                    target_size.width() - 12,
                    target_size.height() - 12,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self._photo_cache[cache_key] = scaled

                return scaled

        icon_name = icon_for_category(product.category)
        cached_icon = self._icon_cache.get(icon_name)

        if cached_icon is None:
            cached_icon = load_icon(
                icon_name,
                color=_COLOR_PLACEHOLDER_ICON,
                size=_PLACEHOLDER_ICON_SIZE,
            ).pixmap(
                QSize(_PLACEHOLDER_ICON_SIZE, _PLACEHOLDER_ICON_SIZE)
            )
            self._icon_cache[icon_name] = cached_icon

        return cached_icon

    def _paint_pill(self, painter, rect, bg_color, text_color, text, font):
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignCenter, text)

    def _paint_badge(self, painter, product, photo_rect):
        text, variant = resolve_stock_status(
            product.quantity, product.min_quantity
        )
        bg_color, text_color = _BADGE_COLORS[variant]

        font = QFont(painter.font())
        font.setPointSize(9)
        font.setBold(True)

        metrics = QFontMetrics(font)
        badge_width = metrics.horizontalAdvance(text) + 24
        badge_height = 26

        badge_rect = QRect(
            photo_rect.right() - badge_width - 10,
            photo_rect.top() + 10,
            badge_width,
            badge_height,
        )

        self._paint_pill(
            painter, badge_rect, bg_color, text_color, text, font
        )

    def _paint_cart_marker(self, painter, product, quantity, photo_rect):
        """Fotosuratning chap tepasida "2 ta" / "2,5 kg" — mahsulot
        allaqachon korzinada ekanini bir qarashda ko'rsatadi."""

        unit = (product.unit or "").strip()

        if is_weight_unit(unit):
            text = f"{format_quantity(quantity)} {unit}"
        else:
            text = f"{format_quantity(quantity)} ta"

        font = QFont(painter.font())
        font.setPointSize(10)
        font.setBold(True)

        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text) + 26

        marker_rect = QRect(
            photo_rect.left() + 10, photo_rect.top() + 10, width, 28
        )

        self._paint_pill(
            painter, marker_rect, _COLOR_INK, _COLOR_ON_DARK, text, font
        )

    def _paint_text(
        self, painter, option, product, content_rect, photo_rect
    ):
        name_font = QFont(option.font)
        name_font.setPointSize(12)
        name_font.setBold(True)

        # Narx va qoldiq qat'iy joyda turishi uchun nom 2 qator bilan
        # cheklanadi (uzun nom qolgan qatorlarni surib yubormasin).
        name_rect = QRect(
            content_rect.left(),
            photo_rect.bottom() + 10,
            content_rect.width(),
            46,
        )
        painter.setFont(name_font)
        painter.setPen(_COLOR_NAME)
        painter.setClipRect(name_rect)
        painter.drawText(
            name_rect,
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            product.name or "",
        )
        painter.setClipping(False)

        # Narx: raqam yirik, "so'm" kichik va xira — pul miqdori
        # birinchi o'qiladi.
        price_font = QFont(option.font)
        price_font.setPointSize(15)
        price_font.setBold(True)

        currency_font = QFont(option.font)
        currency_font.setPointSize(10)

        price_text = format_money(product.sell_price)
        price_width = QFontMetrics(price_font).horizontalAdvance(price_text)

        price_rect = QRect(
            content_rect.left(),
            name_rect.bottom() + 2,
            content_rect.width(),
            32,
        )
        painter.setFont(price_font)
        painter.setPen(_COLOR_PRICE)
        painter.drawText(
            price_rect, Qt.AlignLeft | Qt.AlignVCenter, price_text
        )

        painter.setFont(currency_font)
        painter.setPen(_COLOR_MUTED)
        painter.drawText(
            price_rect.adjusted(price_width + 5, 0, 0, 0),
            Qt.AlignLeft | Qt.AlignVCenter,
            "so'm",
        )

        unit = (product.unit or "dona").strip() or "dona"
        stock_font = QFont(option.font)
        stock_font.setPointSize(10)

        stock_rect = QRect(
            content_rect.left(),
            content_rect.bottom() - 24,
            content_rect.width() - _ADD_BUTTON_SIZE - 8,
            24,
        )
        painter.setFont(stock_font)
        painter.setPen(_COLOR_MUTED)
        painter.drawText(
            stock_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{format_quantity(product.quantity)} {unit}",
        )

    def _paint_add_button(self, painter, content_rect):
        """Yumaloq izumrud "+": kartochkani bosish 1 ta qo'shishini
        ko'rsatadi. Alohida bosiladigan zona emas — butun kartochka
        bosiladi (kassirga aniq nishonga olish shart emas)."""

        button_rect = QRect(
            content_rect.right() - _ADD_BUTTON_SIZE + 1,
            content_rect.bottom() - _ADD_BUTTON_SIZE + 1,
            _ADD_BUTTON_SIZE,
            _ADD_BUTTON_SIZE,
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(_COLOR_ACCENT)
        painter.drawEllipse(button_rect)

        center = QPointF(button_rect.center()) + QPointF(0.5, 0.5)
        arm = 10

        painter.setPen(QPen(_COLOR_ON_DARK, 2.6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(
            QPointF(center.x() - arm, center.y()),
            QPointF(center.x() + arm, center.y()),
        )
        painter.drawLine(
            QPointF(center.x(), center.y() - arm),
            QPointF(center.x(), center.y() + arm),
        )
