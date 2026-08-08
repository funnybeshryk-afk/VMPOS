from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.product_service import ProductService
from app.ui.stock_receipt_dialog import StockReceiptDialog
from app.ui.stock_receipts_dialog import StockReceiptsDialog
from app.utils.formatters import format_quantity
from app.widgets.badge import stock_status_badge
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton
from app.widgets.summary_card import SummaryCard


class WarehousePage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Ombor")
        title.setObjectName("pageTitle")

        summary_layout = QHBoxLayout()

        self.total_products_card = SummaryCard("Jami mahsulotlar")
        self.low_stock_card = SummaryCard("Kam qolgan", "warning")
        self.out_of_stock_card = SummaryCard("Tugagan", "danger")

        summary_layout.addWidget(self.total_products_card)
        summary_layout.addWidget(self.low_stock_card)
        summary_layout.addWidget(self.out_of_stock_card)

        buttons_layout = QHBoxLayout()

        # "Tovar qabul qilish" — bu sahifadagi eng ko'p bosiladigan
        # amal (ombordan tovar kirimi), shuning uchun yagona qora
        # PrimaryButton. Qolgan ikkitasi — yordamchi amallar.
        self.receive_button = PrimaryButton("Tovar qabul qilish")
        self.receive_button.clicked.connect(self.receive_stock)

        self.history_button = SecondaryButton("Qabul tarixi")
        self.history_button.clicked.connect(self.open_receipts_history)

        self.refresh_button = SecondaryButton("Yangilash")
        self.refresh_button.clicked.connect(self.load_products)

        buttons_layout.addWidget(self.receive_button)
        buttons_layout.addWidget(self.history_button)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addStretch()

        self.products_table = DataTable()
        self.products_table.verticalHeader().setDefaultSectionSize(36)
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Shtrix-kod",
            "Mahsulot",
            "Qoldiq",
            "Minimal qoldiq",
            "Holat",
        ])
        self.products_table.pin_column_width(4)

        main_layout.addWidget(title)
        main_layout.addLayout(summary_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.products_table)

        self.load_products()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_products()

    def load_products(self):
        products = ProductService.get_all_products()

        self.products_table.setRowCount(len(products))

        low_stock_count = 0
        out_of_stock_count = 0

        for row, product in enumerate(products):
            if product.quantity <= 0:
                out_of_stock_count += 1
            elif product.quantity <= product.min_quantity:
                low_stock_count += 1

            barcode_item = QTableWidgetItem(product.barcode or "")
            barcode_item.setData(Qt.UserRole, product.id)

            self.products_table.setItem(row, 0, barcode_item)
            self.products_table.setItem(
                row, 1, QTableWidgetItem(product.name)
            )
            self.products_table.setItem(
                row,
                2,
                QTableWidgetItem(format_quantity(product.quantity)),
            )
            self.products_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_quantity(product.min_quantity)
                ),
            )
            self.products_table.setCellWidget(
                row,
                4,
                stock_status_badge(
                    product.quantity,
                    product.min_quantity,
                ),
            )

        self.total_products_card.set_value(len(products))
        self.low_stock_card.set_value(low_stock_count)
        self.out_of_stock_card.set_value(out_of_stock_count)

    def receive_stock(self):
        current_row = self.products_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Qabul qilish uchun mahsulotni tanlang.",
            )
            return

        product_id = self.products_table.item(
            current_row,
            0,
        ).data(Qt.UserRole)

        product = ProductService.get_product(product_id)

        if product is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mahsulot topilmadi.",
            )
            return

        dialog = StockReceiptDialog(product, self)

        if not dialog.exec():
            return

        try:
            updated_product = ProductService.add_stock(
                product_id,
                dialog.get_quantity(),
                dialog.get_supplier_id(),
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        self.load_products()

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"{updated_product.name} qoldig'i: "
            f"{format_quantity(updated_product.quantity)}",
        )

    def open_receipts_history(self):
        dialog = StockReceiptsDialog(self)
        dialog.exec()