from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QTableWidgetItem

from app.services.product_service import ProductService
from app.utils.formatters import format_money, format_quantity
from app.widgets.badge import stock_status_badge
from app.widgets.data_table import DataTable


class ProductsTable(DataTable):
    def __init__(self):
        super().__init__()

        self.products = []

        self.setColumnCount(6)

        self.setHorizontalHeaderLabels([
            "Shtrix kod",
            "Nomi",
            "Kategoriya",
            "Narxi",
            "Qoldiq",
            "Holat",
        ])
        self.pin_column_width(5)

        # Narx yorliqlarini bir nechta mahsulot uchun birdaniga chop
        # etish mumkin bo'lishi kerak — shuning uchun bu yerda,
        # boshqa sahifalardan farqli, ko'p qatorli tanlov yoqilgan
        # (Ctrl/Shift bilan). Tahrirlash/o'chirish currentRow() dan
        # foydalanadi va bu rejimda ham xuddi shunday ishlayveradi.
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def get_selected_products(self):
        selected_rows = sorted({
            index.row() for index in self.selectedIndexes()
        })

        selected_ids = [
            self.item(row, 0).data(Qt.UserRole)
            for row in selected_rows
        ]

        return [
            product
            for product in self.products
            if product.id in selected_ids
        ]

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
                QTableWidgetItem(format_money(product.sell_price)),
            )
            self.setItem(
                row,
                4,
                QTableWidgetItem(
                    format_quantity(product.quantity)
                ),
            )
            self.setCellWidget(
                row,
                5,
                stock_status_badge(
                    product.quantity,
                    product.min_quantity,
                ),
            )