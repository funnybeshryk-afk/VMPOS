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


def stock_status_badge(quantity, min_quantity):
    if quantity <= 0:
        return badge_cell("Tugagan", "danger")

    if min_quantity and quantity <= min_quantity:
        return badge_cell("Kam qoldi", "warning")

    return badge_cell("Yetarli", "success")