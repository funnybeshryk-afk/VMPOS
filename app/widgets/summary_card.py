from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

_VALUE_OBJECT_NAMES = {
    "default": "statValue",
    "warning": "statValueWarning",
    "danger": "statValueDanger",
}


class SummaryCard(QFrame):
    """Карточка-показатель для сводки в шапке страницы: подпись + число.

    Раньше важность показателя передавалась цветом всего фона карточки
    (пять карточек — пять случайных цветов). Теперь карточка всегда
    белая, а важность — только у числа: обычное, жёлтое или красное.
    Так сводка выглядит одним связным блоком, а не витражом.
    """

    def __init__(self, caption, variant="default"):
        super().__init__()

        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        caption_label = QLabel(caption)
        caption_label.setObjectName("statCaption")

        self.value_label = QLabel("0")
        self.value_label.setObjectName(
            _VALUE_OBJECT_NAMES.get(variant, "statValue")
        )

        layout.addWidget(caption_label)
        layout.addWidget(self.value_label)

        self.setMinimumHeight(70)

    def set_value(self, value):
        self.value_label.setText(str(value))
