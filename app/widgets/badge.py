from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

_VARIANT_OBJECT_NAMES = {
    "success": "badgeSuccess",
    "warning": "badgeWarning",
    "danger": "badgeDanger",
    "neutral": "badgeNeutral",
}


class StatusBadge(QLabel):
    def __init__(self, text: str, variant: str = "neutral"):
        super().__init__(text)

        self.setObjectName(
            _VARIANT_OBJECT_NAMES.get(variant, "badgeNeutral")
        )

        self.setAlignment(Qt.AlignCenter)

        font = self.font()
        font.setStyleStrategy(
            QFont.PreferAntialias | QFont.NoSubpixelAntialias
        )
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)

        self.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed,
        )

        self.setMinimumHeight(26)

        self.adjustSize()


def set_badge_variant(label, text, variant="neutral"):
    label.setText(text)

    label.setObjectName(
        _VARIANT_OBJECT_NAMES.get(variant, "badgeNeutral")
    )

    label.style().unpolish(label)
    label.style().polish(label)

    label.adjustSize()


def badge_cell(text, variant="neutral"):
    wrapper = QWidget()
    wrapper.setObjectName("badgeCell")

    wrapper.setAttribute(
        Qt.WA_TransparentForMouseEvents,
        True,
    )

    layout = QHBoxLayout(wrapper)

    layout.setContentsMargins(6, 3, 6, 3)
    layout.setSpacing(0)
    layout.setAlignment(Qt.AlignCenter)

    badge = StatusBadge(text, variant)

    layout.addWidget(badge)

    wrapper.setMinimumHeight(32)

    return wrapper


def resolve_stock_status(quantity, min_quantity):
    """(matn, variant) — qoldiq holatining sof (vidjetsiz) hisobi.

    stock_status_badge() (jadval/ro'yxat, QWidget) va
    ProductCardDelegate (panjara, qo'lda QPainter chizuvi) shu bitta
    funksiyadan foydalanadi — bosqichlar bitta joyda.
    """

    if quantity <= 0:
        return "Tugagan", "danger"

    if min_quantity and quantity <= min_quantity:
        return "Kam qoldi", "warning"

    return "Yetarli", "success"


def stock_status_badge(quantity, min_quantity):
    text, variant = resolve_stock_status(quantity, min_quantity)

    return badge_cell(text, variant)


_SALE_STATUS_LABELS = {
    "completed": ("Yakunlangan", "success"),
    "partially_refunded": ("Qisman qaytarilgan", "warning"),
    "refunded": ("To'liq qaytarilgan", "danger"),
}


def resolve_sale_status(status):
    """(matn, variant) — Sale.status uchun, ReportsPage/SaleDetails
    Dialog/ReturnDialog uch joyda bir xil belgilarni ko'rsatishi
    uchun bitta joyda.
    """

    return _SALE_STATUS_LABELS.get(status, (status, "neutral"))