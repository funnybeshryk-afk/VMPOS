from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class DangerButton(QPushButton):
    """Необратимое действие: удаление, отмена продажи.

    В покое выглядит сдержанно — красный текст и бледная рамка.
    Заливку получает при наведении. Так удаление не соперничает
    за внимание с главной кнопкой экрана.

    Внешний вид описан в style.qss (#dangerButton).
    """

    def __init__(self, text, large=False):
        super().__init__(text)

        self.setObjectName("dangerButton")
        self.setCursor(Qt.PointingHandCursor)

        if large:
            self.setProperty("sizeVariant", "lg")
