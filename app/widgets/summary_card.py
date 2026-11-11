from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.utils.icons import load_icon

_VALUE_OBJECT_NAMES = {
    "default": "statValue",
    "warning": "statValueWarning",
    "danger": "statValueDanger",
}

_TOGGLE_ICON_SIZE = 14
_TOGGLE_ICON_COLOR = "#78716c"


class SummaryCard(QFrame):
    """Карточка-показатель для сводки в шапке страницы: подпись + число.

    Раньше важность показателя передавалась цветом всего фона карточки
    (пять карточек — пять случайных цветов). Теперь карточка всегда
    белая, а важность — только у числа: обычное, жёлтое или красное.
    Так сводка выглядит одним связным блоком, а не витражом.

    maskable=True — для конфиденциальных сумм (например, "Ombor
    qiymati"): значение по умолчанию скрыто под mask_text, глаз-иконка
    рядом раскрывает/прячет его. Реальное значение хранится отдельно
    (_real_text) и никогда не участвует в maскировке напрямую — так
    set_value() можно вызывать сколько угодно (обновление данных), не
    сбрасывая текущее скрыто/показано состояние.
    """

    def __init__(
        self,
        caption,
        variant="default",
        maskable=False,
        mask_text="••••••",
    ):
        super().__init__()

        self.setObjectName("statCard")

        self._maskable = maskable
        self._mask_text = mask_text
        self._revealed = not maskable
        self._real_text = "0"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        caption_label = QLabel(caption)
        caption_label.setObjectName("statCaption")

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(6)

        self.value_label = QLabel("0")
        self.value_label.setObjectName(
            _VALUE_OBJECT_NAMES.get(variant, "statValue")
        )

        value_row.addWidget(self.value_label)

        if maskable:
            self.toggle_button = QPushButton()
            self.toggle_button.setObjectName("summaryCardToggle")
            self.toggle_button.setCursor(Qt.PointingHandCursor)
            self.toggle_button.setFixedSize(22, 22)
            self.toggle_button.clicked.connect(
                self._toggle_revealed
            )

            value_row.addWidget(self.toggle_button)
            self._update_toggle_icon()

        value_row.addStretch()

        layout.addWidget(caption_label)
        layout.addLayout(value_row)

        self.setMinimumHeight(70)

    def set_value(self, value):
        self._real_text = str(value)
        self._refresh_display()

    def _toggle_revealed(self):
        self._revealed = not self._revealed
        self._refresh_display()
        self._update_toggle_icon()

    def _refresh_display(self):
        self.value_label.setText(
            self._real_text if self._revealed else self._mask_text
        )

    def _update_toggle_icon(self):
        icon_name = "eye-off" if self._revealed else "eye"
        self.toggle_button.setIcon(
            load_icon(
                icon_name,
                color=_TOGGLE_ICON_COLOR,
                size=_TOGGLE_ICON_SIZE,
            )
        )
        self.toggle_button.setIconSize(
            QSize(_TOGGLE_ICON_SIZE, _TOGGLE_ICON_SIZE)
        )
