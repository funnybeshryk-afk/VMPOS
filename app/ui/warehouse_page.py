from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.product_service import ProductService
from app.ui.stock_receipt_dialog import StockReceiptDialog
from app.ui.stock_receipts_dialog import StockReceiptsDialog
from app.utils.formatters import format_quantity


class WarehousePage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Ombor")
        title.setObjectName("pageTitle")

        self.refresh_button = QPushButton("Yangilash")
        self.refresh_button.clicked.connect(self.load_products)

        self.receive_button = QPushButton("Tovar qabul qilish")
        self.receive_button.clicked.connect(self.receive_stock)

        self.history_button = QPushButton("Qabul tarixi")
        self.history_button.clicked.connect(self.open_receipts_history)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Shtrix-kod",
            "Mahsulot",
            "Qoldiq",
            "Minimal qoldiq",
            "Holat",
        ])

        self.products_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.products_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.products_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.products_table.verticalHeader().setVisible(False)
        self.products_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        main_layout.addWidget(title)
        main_layout.addWidget(self.refresh_button)
        main_layout.addWidget(self.receive_button)
        main_layout.addWidget(self.history_button)
        main_layout.addWidget(self.products_table)

        self.load_products()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_products()

    def load_products(self):
        products = ProductService.get_all_products()

        self.products_table.setRowCount(len(products))

        for row, product in enumerate(products):
            if product.quantity <= 0:
                status = "Yo'q"
                color = QColor("#ffcdd2")

            elif product.quantity <= product.min_quantity:
                status = "Kam qoldi"
                color = QColor("#fff3cd")

            else:
                status = "Yetarli"
                color = QColor("#d9f2df")

            barcode_item = QTableWidgetItem(product.barcode or "")
            barcode_item.setData(Qt.UserRole, product.id)

            items = [
                barcode_item,
                QTableWidgetItem(product.name),
                QTableWidgetItem(
                    format_quantity(product.quantity)
                ),
                QTableWidgetItem(
                    format_quantity(product.min_quantity)
                ),
                QTableWidgetItem(status),
            ]

            for column, item in enumerate(items):
                item.setBackground(color)
                self.products_table.setItem(row, column, item)

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