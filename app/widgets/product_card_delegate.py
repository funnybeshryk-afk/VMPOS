from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt
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
from app.widgets.badge import resolve_stock_status
from app.widgets.product_list_model import ProductRole

CARD_SIZE = QSize(180, 210)

_CARD_MARGIN = 6
_PADDING = 10
_PHOTO_HEIGHT = 96
_PLACEHOLDER_ICON_SIZE = 36

# QListView virtuallashtirilgan bo'lishi uchun kartochka setIndexWidget()
# orqali haqiqiy QWidget bilan emas, shu delegate ichida QPainter bilan
# qo'lda chiziladi — shuning uchun QSS bu yerga yetib bormaydi. Ranglar
# style.qss'dagi #productCard*/#badge* qiymatlari bilan qo'lda
# muvofiqlashtirilgan (bitta manba emas, lekin muqobili yo'q).
_COLOR_CARD_BG = QColor("#ffffff")
_COLOR_CARD_BORDER = QColor("#e2e8f0")
_COLOR_CARD_BORDER_HOVER = QColor("#94a3b8")
_COLOR_PHOTO_BG = QColor("#f8fafc")
_COLOR_NAME = QColor("#0f172a")
_COLOR_PRICE = QColor("#0f172a")
_COLOR_STOCK = QColor("#64748b")
_COLOR_PLACEHOLDER_ICON = "#94a3b8"

_BADGE_COLORS = {
    "success": (QColor("#f0fdf4"), QColor("#14532d")),
    "warning": (QColor("#fef3c7"), QColor("#92400e")),
    "danger": (QColor("#fee2e2"), QColor("#991b1b")),
    "neutral": (QColor("#f1f5f9"), QColor("#1e293b")),
}


class ProductCardDelegate(QStyledItemDelegate):
    """Katalog kartochkasini qo'lda chizadigan delegate.

    Foto/ikonka pixmaplari keshlanadi (self._photo_cache/_icon_cache)
    — aks holda har bir paint() chaqiruvida (masalan skroll paytida)
    diskdan qayta o'qish yoki SVG'ni qayta render qilish kerak
    bo'lardi, bu virtualizatsiyaning o'zini sekinlashtirib qo'yardi.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._photo_cache = {}
        self._icon_cache = {}

    def sizeHint(self, option, index):
        return CARD_SIZE

    def paint(self, painter, option, index):
        product = index.data(ProductRole)

        if product is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        card_rect = option.rect.adjusted(
            _CARD_MARGIN, _CARD_MARGIN, -_CARD_MARGIN, -_CARD_MARGIN
        )
        is_hovered = bool(option.state & QStyle.State_MouseOver)

        painter.setPen(
            QPen(
                _COLOR_CARD_BORDER_HOVER
                if is_hovered
                else _COLOR_CARD_BORDER,
                1,
            )
        )
        painter.setBrush(_COLOR_CARD_BG)
        painter.drawRoundedRect(card_rect, 12, 12)

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
        self._paint_text(painter, option, product, content_rect, photo_rect)

        painter.restore()

    def _paint_photo(self, painter, product, photo_rect):
        painter.setPen(Qt.NoPen)
        painter.setBrush(_COLOR_PHOTO_BG)
        painter.drawRoundedRect(photo_rect, 8, 8)

        pixmap = self._resolve_pixmap(product, photo_rect.size())

        pixmap_rect = pixmap.rect()
        pixmap_rect.moveCenter(photo_rect.center())

        painter.setClipRect(photo_rect)
        painter.drawPixmap(pixmap_rect.topLeft(), pixmap)
        painter.setClipping(False)

    def _resolve_pixmap(self, product, target_size):
        if product.image_path and Path(product.image_path).is_file():
            cache_key = (
                "photo",
                product.image_path,
                target_size.width(),
                target_size.height(),
            )
            cached = self._photo_cache.get(cache_key)

            if cached is not None:
                return cached

            candidate = QPixmap(product.image_path)

            if not candidate.isNull():
                # KeepAspectRatioByExpanding to'ldirib, chetlarini
                # kesib tashlar edi (masalan tarvuz surati tepa-
                # pastdan kesilib qolardi). KeepAspectRatio esa
                # to'liq sig'diradi — natijada rasm atrofida ozgina
                # bo'sh joy qolishi mumkin, lekin hech narsa
                # kesilmaydi, bu kesilgan suratdan yaxshiroq.
                scaled = candidate.scaled(
                    target_size.width(),
                    target_size.height(),
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

    def _paint_badge(self, painter, product, photo_rect):
        text, variant = resolve_stock_status(
            product.quantity, product.min_quantity
        )
        bg_color, text_color = _BADGE_COLORS[variant]

        font = QFont(painter.font())
        font.setPointSize(8)
        font.setBold(True)

        metrics = QFontMetrics(font)
        badge_width = metrics.horizontalAdvance(text) + 16
        badge_height = 20

        badge_rect = QRect(
            photo_rect.right() - badge_width - 6,
            photo_rect.top() + 6,
            badge_width,
            badge_height,
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(badge_rect, 10, 10)

        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(badge_rect, Qt.AlignCenter, text)

    def _paint_text(
        self, painter, option, product, content_rect, photo_rect
    ):
        name_font = QFont(option.font)
        name_font.setPointSize(10)
        name_font.setBold(True)

        name_rect = QRect(
            content_rect.left(),
            photo_rect.bottom() + 8,
            content_rect.width(),
            32,
        )
        painter.setFont(name_font)
        painter.setPen(_COLOR_NAME)
        painter.drawText(
            name_rect,
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            product.name or "",
        )

        price_font = QFont(option.font)
        price_font.setPointSize(11)
        price_font.setBold(True)

        price_rect = QRect(
            content_rect.left(),
            name_rect.bottom() + 2,
            content_rect.width(),
            18,
        )
        painter.setFont(price_font)
        painter.setPen(_COLOR_PRICE)
        painter.drawText(
            price_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{format_money(product.sell_price)} so'm",
        )

        unit = (product.unit or "dona").strip() or "dona"
        stock_font = QFont(option.font)
        stock_font.setPointSize(9)

        stock_rect = QRect(
            content_rect.left(),
            price_rect.bottom() + 2,
            content_rect.width(),
            16,
        )
        painter.setFont(stock_font)
        painter.setPen(_COLOR_STOCK)
        painter.drawText(
            stock_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{format_quantity(product.quantity)} {unit}",
        )
