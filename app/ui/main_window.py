from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.resources.language import TEXT
from app.ui.products_page import ProductsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VMPOS")
        self.resize(1200, 700)

        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        content_layout = QHBoxLayout()

        self.menu = QListWidget()
        self.menu.setFixedWidth(220)

        self.menu.addItems([
            TEXT["sale"],
            TEXT["products"],
            TEXT["warehouse"],
            TEXT["reports"],
            TEXT["customers"],
            TEXT["suppliers"],
            TEXT["settings"],
        ])

        self.workspace = QStackedWidget()

        self.products_page = ProductsPage()
        self.workspace.addWidget(self.products_page)

        self.menu.currentRowChanged.connect(self.change_page)

        content_layout.addWidget(self.menu)
        content_layout.addWidget(self.workspace)

        self.status = QLabel(TEXT["ready"])

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status)

        self.menu.setCurrentRow(1)

    def change_page(self, index):
        if index == 1:
            self.workspace.setCurrentWidget(self.products_page)