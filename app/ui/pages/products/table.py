from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from app.services.product_service import ProductService


class ProductsTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.products = []

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "Shtrix kod",
            "Nomi",
            "Kategoriya",
            "Narxi",
            "Qoldiq",
        ])

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.verticalHeader().setVisible(False)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setShowGrid(False)

    def load_data(self):
        self.products = ProductService.get_all_products()
        self.populate_table(self.products)

    def search_products(self, text):
        text = text.strip().lower()

        if not text:
            self.populate_table(self.products)
            return

        filtered_products = []

        for product in self.products:
            barcode = product.barcode.lower() if product.barcode else ""
            name = product.name.lower() if product.name else ""
            category = product.category.lower() if product.category else ""

            if (
                text in barcode
                or text in name
                or text in category
            ):
                filtered_products.append(product)

        self.populate_table(filtered_products)

    def populate_table(self, products):
        self.setRowCount(len(products))

        for row, product in enumerate(products):
            barcode = QTableWidgetItem(product.barcode or "")
            barcode.setData(Qt.UserRole, product.id)

            self.setItem(row, 0, barcode)
            self.setItem(row, 1, QTableWidgetItem(product.name or ""))
            self.setItem(
                row,
                2,
                QTableWidgetItem(product.category or ""),
            )
            self.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"{product.sell_price:,.0f}".replace(",", " ")
                ),
            )
            self.setItem(
                row,
                4,
                QTableWidgetItem(f"{product.quantity:g}"),
            )