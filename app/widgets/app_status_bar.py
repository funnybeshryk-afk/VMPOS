from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.widgets.badge import StatusBadge
from app.i18n import tr

_HOTKEYS = [
    ("F2", tr("Qidiruv")),
    ("F5", tr("Bekor qilish")),
    ("F4", tr("To'lov")),
]

_DEVICES = [tr("Skaner"), tr("Tarozi"), tr("Printer")]


class AppStatusBar(QWidget):
    """Pastki qatordagi tezkor klavishlar va uskunalar holati.

    Uskunalar bilan haqiqiy aloqa hali ulanmagan — birinchi bosqichda
    holat doim "Ulanmagan" bo'lib qattiq yoziladi. Haqiqiy tekshiruv
    keyinroq shu klassga qo'shiladi, sahifaning qolgan qismiga
    tegmasdan.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("statusBar")
        # Qt'da QWidget'dan meros olingan o'z klassi QSS fonini
        # (#statusBar) FAQAT shu atribut bilan chizadi — busiz qator
        # fonsiz va chegarasiz qolgan edi.
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(20)

        hotkeys_text = "    ".join(
            f"{key} — {label}" for key, label in _HOTKEYS
        )
        hotkeys_label = QLabel(hotkeys_text)
        hotkeys_label.setObjectName("statusBarHint")

        layout.addWidget(hotkeys_label)
        layout.addStretch()

        for device_name in _DEVICES:
            layout.addWidget(
                self._build_device_indicator(device_name)
            )

    @staticmethod
    def _build_device_indicator(device_name):
        container = QWidget()
        container.setObjectName("statusBarItem")

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)

        name_label = QLabel(device_name)
        name_label.setObjectName("statusBarHint")

        status_badge = StatusBadge(tr("Ulanmagan"), "neutral")

        container_layout.addWidget(name_label)
        container_layout.addWidget(status_badge)

        return container
