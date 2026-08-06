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
from app.ui.customers_page import CustomersPage
from app.ui.products_page import ProductsPage
from app.ui.reports_page import ReportsPage
from app.ui.sale_page import SalePage
from app.ui.suppliers_page import SuppliersPage
from app.ui.warehouse_page import WarehousePage


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

        self.sale_page = SalePage()
        self.workspace.addWidget(self.sale_page)

        self.products_page = ProductsPage()
        self.workspace.addWidget(self.products_page)

        self.warehouse_page = WarehousePage()
        self.workspace.addWidget(self.warehouse_page)

        self.reports_page = ReportsPage()
        self.workspace.addWidget(self.reports_page)

        self.customers_page = CustomersPage()
        self.workspace.addWidget(self.customers_page)

        self.suppliers_page = SuppliersPage()
        self.workspace.addWidget(self.suppliers_page)

        self.menu.currentRowChanged.connect(self.change_page)

        content_layout.addWidget(self.menu)
        content_layout.addWidget(self.workspace)

        self.status = QLabel(TEXT["ready"])

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status)

        self.menu.setCurrentRow(1)

    def change_page(self, index):
        if index == 0:
            self.sale_page.load_products()
            self.workspace.setCurrentWidget(self.sale_page)

        elif index == 1:
            self.workspace.setCurrentWidget(self.products_page)

        elif index == 2:
            self.workspace.setCurrentWidget(self.warehouse_page)

        elif index == 3:
            self.workspace.setCurrentWidget(self.reports_page)

        elif index == 4:
            self.workspace.setCurrentWidget(self.customers_page)

        elif index == 5:
            self.workspace.setCurrentWidget(self.suppliers_page)