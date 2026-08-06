from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.services.product_service import ProductService
from app.ui.pages.products.table import ProductsTable
from app.ui.product_dialog import ProductDialog
from app.utils.formatters import format_money
from app.widgets.danger_button import DangerButton
from app.widgets.primary_button import PrimaryButton


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Mahsulotlar")
        title.setObjectName("pageTitle")

        summary_layout = QHBoxLayout()

        self.total_products_card = self.create_summary_card(
            "Jami mahsulotlar",
            "#e8f5e9",
        )
        self.categories_card = self.create_summary_card(
            "Kategoriyalar",
            "#e3f2fd",
        )
        self.low_stock_card = self.create_summary_card(
            "Kam qolgan",
            "#fff3cd",
        )
        self.out_of_stock_card = self.create_summary_card(
            "Tugagan",
            "#ffcdd2",
        )
        self.stock_value_card = self.create_summary_card(
            "Ombor qiymati",
            "#f3e5f5",
        )

        summary_layout.addWidget(self.total_products_card)
        summary_layout.addWidget(self.categories_card)
        summary_layout.addWidget(self.low_stock_card)
        summary_layout.addWidget(self.out_of_stock_card)
        summary_layout.addWidget(self.stock_value_card)

        top_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Qidirish...")

        add_btn = PrimaryButton("Qo'shish")
        add_btn.clicked.connect(self.open_add_dialog)

        edit_btn = PrimaryButton("Tahrirlash")
        edit_btn.clicked.connect(self.edit_product)

        delete_btn = DangerButton("O'chirish")
        delete_btn.clicked.connect(self.delete_product)

        top_layout.addWidget(self.search)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(delete_btn)

        self.table = ProductsTable()
        self.refresh_data()

        self.search.textChanged.connect(self.table.search_products)

        main_layout.addWidget(title)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

    def create_summary_card(self, title, color):
        card = QLabel()
        card.setAlignment(Qt.AlignCenter)
        card.setMinimumHeight(70)
        card.setStyleSheet(
            f"""
            background-color: {color};
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
            font-weight: 600;
            """
        )
        card.setText(f"{title}\n0")

        return card

    def refresh_data(self):
        self.table.load_data()
        self.table.search_products(self.search.text())
        self.update_summary_cards()

    def update_summary_cards(self):
        products = self.table.products

        total_products = len(products)

        categories = {
            product.category.strip()
            for product in products
            if product.category and product.category.strip()
        }

        low_stock_count = sum(
            1
            for product in products
            if (
                product.quantity > 0
                and product.quantity <= product.min_quantity
            )
        )

        out_of_stock_count = sum(
            1
            for product in products
            if product.quantity <= 0
        )

        stock_value = sum(
            (product.buy_price or 0) * (product.quantity or 0)
            for product in products
        )

        self.total_products_card.setText(
            f"Jami mahsulotlar\n{total_products}"
        )
        self.categories_card.setText(
            f"Kategoriyalar\n{len(categories)}"
        )
        self.low_stock_card.setText(
            f"Kam qolgan\n{low_stock_count}"
        )
        self.out_of_stock_card.setText(
            f"Tugagan\n{out_of_stock_count}"
        )
        self.stock_value_card.setText(
            "Ombor qiymati\n"
            f"{format_money(stock_value)} so'm"
        )

    def open_add_dialog(self):
        dialog = ProductDialog()

        if dialog.exec():
            data = dialog.get_data()
            barcode_was_empty = not data["barcode"].strip()

            try:
                product = ProductService.create_product(data)

            except ValueError as error:
                QMessageBox.warning(
                    self,
                    "Diqqat",
                    str(error),
                )
                return

            self.refresh_data()

            if barcode_was_empty:
                QMessageBox.information(
                    self,
                    "Mahsulot saqlandi",
                    "Avtomatik shtrix-kod berildi:\n"
                    f"{product.barcode}",
                )

    def edit_product(self):
        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.information(
                self,
                "Diqqat",
                "Tahrirlash uchun mahsulotni tanlang.",
            )
            return

        product_id = self.table.item(current_row, 0).data(Qt.UserRole)
        product = ProductService.get_product(product_id)

        dialog = ProductDialog(product)

        if dialog.exec():
            try:
                ProductService.update_product(
                    product_id,
                    dialog.get_data(),
                )

            except ValueError as error:
                QMessageBox.warning(
                    self,
                    "Diqqat",
                    str(error),
                )
                return

            self.refresh_data()

    def delete_product(self):
        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.information(
                self,
                "Diqqat",
                "O'chirish uchun mahsulotni tanlang.",
            )
            return

        product_id = self.table.item(current_row, 0).data(Qt.UserRole)
        product_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            f'"{product_name}" o‘chirmoqchimisiz?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            ProductService.delete_product(product_id)
            self.refresh_data()