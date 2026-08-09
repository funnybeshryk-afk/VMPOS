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
from app.ui.label_print_dialog import LabelPrintDialog
from app.ui.pages.products.table import ProductsTable
from app.ui.product_dialog import ProductDialog
from app.utils.formatters import format_money
from app.widgets.danger_button import DangerButton
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton
from app.widgets.summary_card import SummaryCard


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Mahsulotlar")
        title.setObjectName("pageTitle")

        summary_layout = QHBoxLayout()

        self.total_products_card = SummaryCard("Jami mahsulotlar")
        self.categories_card = SummaryCard("Kategoriyalar")
        self.low_stock_card = SummaryCard("Kam qolgan", "warning")
        self.out_of_stock_card = SummaryCard("Tugagan", "danger")
        self.stock_value_card = SummaryCard(
            "Ombor qiymati", maskable=True, mask_text="•••••• so'm"
        )

        summary_layout.addWidget(self.total_products_card)
        summary_layout.addWidget(self.categories_card)
        summary_layout.addWidget(self.low_stock_card)
        summary_layout.addWidget(self.out_of_stock_card)
        summary_layout.addWidget(self.stock_value_card)

        top_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setObjectName("searchInput")
        self.search.setPlaceholderText("Qidirish...")

        # "Qo'shish" — bu sahifadagi eng ko'p bosiladigan amal,
        # shuning uchun yagona qora PrimaryButton shu yerda.
        # Tahrirlash — ikkinchi darajali, SecondaryButton.
        add_btn = PrimaryButton("Qo'shish")
        add_btn.clicked.connect(self.open_add_dialog)

        edit_btn = SecondaryButton("Tahrirlash")
        edit_btn.clicked.connect(self.edit_product)

        delete_btn = DangerButton("O'chirish")
        delete_btn.clicked.connect(self.delete_product)

        labels_btn = SecondaryButton("Narx yorliqlari")
        labels_btn.clicked.connect(self.open_label_print_dialog)

        top_layout.addWidget(self.search)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(edit_btn)
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(labels_btn)

        self.table = ProductsTable()
        self.refresh_data()

        self.search.textChanged.connect(self.table.search_products)

        main_layout.addWidget(title)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

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

        self.total_products_card.set_value(total_products)
        self.categories_card.set_value(len(categories))
        self.low_stock_card.set_value(low_stock_count)
        self.out_of_stock_card.set_value(out_of_stock_count)
        self.stock_value_card.set_value(
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
        price_tiers = ProductService.get_price_tiers(product_id)

        dialog = ProductDialog(product, price_tiers)

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

    def open_label_print_dialog(self):
        selected_products = self.table.get_selected_products()

        if not selected_products:
            QMessageBox.information(
                self,
                "Diqqat",
                "Narx yorlig'i uchun mahsulot(lar)ni tanlang.",
            )
            return

        dialog = LabelPrintDialog(selected_products, self)
        dialog.exec()