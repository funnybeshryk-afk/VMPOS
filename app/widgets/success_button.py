from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class SuccessButton(QPushButton):
    """Завершение продажи — единственное зелёное место в приложении.

    Зелёный здесь не украшение, а смысл: «деньги приняты».
    Если он появится где-то ещё, он перестанет это значить.

    Внешний вид описан в style.qss (#successButton).
    """

    def __init__(self, text, large=False):
        super().__init__(text)

        self.setObjectName("successButton")
        self.setCursor(Qt.PointingHandCursor)

        if large:
            self.setProperty("sizeVariant", "lg")
