from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)

        self.setMinimumHeight(40)