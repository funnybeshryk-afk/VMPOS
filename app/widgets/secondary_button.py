from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class SecondaryButton(QPushButton):
    """Обычное действие: изменить, обновить, закрыть.

    Это же оформление получает любая кнопка без objectName —
    класс нужен, чтобы намерение было видно в коде страницы.

    Внешний вид описан в style.qss (базовое правило QPushButton).
    """

    def __init__(self, text, large=False):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)

        if large:
            self.setProperty("sizeVariant", "lg")
