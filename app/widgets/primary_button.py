from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    """Главное действие экрана: сохранить, добавить, оформить.

    На одном экране такая кнопка должна быть одна. Если их две —
    значит экран не решил, чего хочет от пользователя.

    Внешний вид описан в style.qss (#primaryButton).
    Здесь мы задаём только роль, не цвета.
    """

    def __init__(self, text, large=False):
        super().__init__(text)

        self.setObjectName("primaryButton")
        self.setCursor(Qt.PointingHandCursor)

        if large:
            self.setProperty("sizeVariant", "lg")
