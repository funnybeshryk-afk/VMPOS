from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class GhostButton(QPushButton):
    """Третьестепенное действие: сброс фильтра, «показать ещё».

    Без рамки и без фона, пока на неё не навели курсор.

    Внешний вид описан в style.qss (#ghostButton).
    """

    def __init__(self, text, large=False):
        super().__init__(text)

        self.setObjectName("ghostButton")
        self.setCursor(Qt.PointingHandCursor)

        if large:
            self.setProperty("sizeVariant", "lg")
