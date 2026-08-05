from PySide6.QtWidgets import QHeaderView, QTableWidget
from app.services.product_service import ProductService
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt
class ProductsTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "Shtrix kod",
            "Nomi",
            "Kategoriya",
            "Narxi",
            "Qoldiq",
        ])

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.verticalHeader().setVisible(False)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setShowGrid(False)

    def load_data(self):
        products = ProductService.get_all_products()

        self.setRowCount(len(products))

        for row, product in enumerate(products):

            barcode = QTableWidgetItem(product.barcode or "")
            barcode.setData(Qt.UserRole, product.id)

            self.setItem(row, 0, barcode)
            self.setItem(row, 1, QTableWidgetItem(product.name or ""))
            self.setItem(row, 2, QTableWidgetItem(product.category or ""))
            self.setItem(row, 3, QTableWidgetItem(f"{product.sell_price:,.0f}".replace(",", " ")))
            self.setItem(row, 4, QTableWidgetItem(f"{product.quantity:g}"))