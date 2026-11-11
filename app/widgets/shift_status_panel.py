from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QWidget

from app.utils.icons import load_icon
from app.widgets.badge import StatusBadge
from app.widgets.secondary_button import SecondaryButton

_PANEL_HEIGHT = 60
_ICON_SIZE = 20
_ICON_COLOR = "#78716c"


class ShiftStatusPanel(QFrame):
    """Sotuv sahifasi tepasidagi joriy smena polosasi.

    Ixcham, bir qatorli — QFrame'ning o'ziga qat'iy balandlik
    (setFixedHeight) qo'yilgan, xuddi CategoryBar'dagi kabi: aks
    holda tashqi QVBoxLayout ortiqcha bo'sh joyni shu panelga ham
    berib, uni keraksiz cho'zib yuboradi.

    "Ко'r" vidjet — ShiftService'ni o'zi chaqirmaydi, ma'lumotni
    sahifa (SalePage) beradi, xuddi CategoryBar kabi.
    """

    openMoliyaRequested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("shiftBar")
        self.setFixedHeight(_PANEL_HEIGHT)

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(4, 0, 4, 0)

        self._stack = QStackedWidget()
        outer_layout.addWidget(self._stack)

        self._shift_view = self._build_shift_view()
        self._no_shift_view = self._build_no_shift_view()

        self._stack.addWidget(self._shift_view)
        self._stack.addWidget(self._no_shift_view)

    def _build_shift_view(self):
        widget = QWidget()

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(
            load_icon(
                "user", color=_ICON_COLOR, size=_ICON_SIZE
            ).pixmap(QSize(_ICON_SIZE, _ICON_SIZE))
        )

        self._cashier_name_label = QLabel()
        self._cashier_name_label.setObjectName("sectionTitle")

        self._shift_meta_label = QLabel()
        self._shift_meta_label.setObjectName("mutedText")

        self._clock_label = QLabel()
        self._clock_label.setObjectName("mutedText")

        layout.addWidget(icon_label)
        layout.addWidget(self._cashier_name_label)
        layout.addWidget(self._shift_meta_label)
        layout.addStretch()
        layout.addWidget(self._clock_label)

        return widget

    def _build_no_shift_view(self):
        widget = QWidget()

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(
            load_icon(
                "alert-triangle",
                color=_ICON_COLOR,
                size=_ICON_SIZE,
            ).pixmap(QSize(_ICON_SIZE, _ICON_SIZE))
        )

        # Tushuntirish matni qatorga sig'maydi — undov (tooltip)
        # sifatida qoldiriladi, ixcham polosa esa faqat holat va
        # amalni ko'rsatadi.
        status_badge = StatusBadge("Smena ochilmagan", "warning")
        status_badge.setToolTip(
            "Sotish uchun avval Moliya bo'limida smenani oching"
        )

        open_moliya_button = SecondaryButton("Moliyaga o'tish")
        open_moliya_button.clicked.connect(
            self.openMoliyaRequested.emit
        )

        layout.addWidget(icon_label)
        layout.addWidget(status_badge)
        layout.addStretch()
        layout.addWidget(open_moliya_button)

        return widget

    def show_shift(self, cashier_name, shift_id, opened_at, now_text):
        opened_text = opened_at.strftime("%H:%M")

        self._cashier_name_label.setText(cashier_name)
        self._shift_meta_label.setText(f"· Smena #{shift_id}")
        self._shift_meta_label.setToolTip(f"Smena ochilgan: {opened_text}")
        self._clock_label.setText(now_text)

        self._stack.setCurrentWidget(self._shift_view)

    def show_no_shift(self):
        self._stack.setCurrentWidget(self._no_shift_view)
