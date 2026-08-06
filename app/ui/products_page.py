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
        self.table.load_data()

        self.search.textChanged.connect(self.table.search_products)

        main_layout.addWidget(title)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

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

            self.table.load_data()
            self.table.search_products(self.search.text())

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

            self.table.load_data()
            self.table.search_products(self.search.text())

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
            f'"{product_name}" mahsulotini o‘chirmoqchimisiz?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            ProductService.delete_product(product_id)
            self.table.load_data()
            self.table.search_products(self.search.text())