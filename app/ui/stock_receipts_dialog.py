from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.product_service import ProductService
from app.utils.formatters import format_quantity


class StockReceiptsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Qabul tarixi")
        self.resize(750, 400)

        main_layout = QVBoxLayout(self)

        self.receipts_table = QTableWidget()
        self.receipts_table.setColumnCount(4)
        self.receipts_table.setHorizontalHeaderLabels([
            "Sana",
            "Mahsulot",
            "Yetkazib beruvchi",
            "Miqdor",
        ])

        self.receipts_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.receipts_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.receipts_table.verticalHeader().setVisible(False)
        self.receipts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        close_button = QPushButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(self.receipts_table)
        main_layout.addWidget(close_button)

        self.load_receipts()

    def load_receipts(self):
        receipts = ProductService.get_stock_receipts()

        self.receipts_table.setRowCount(len(receipts))

        for row, receipt in enumerate(receipts):
            receipt_date = receipt.created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

            self.receipts_table.setItem(
                row,
                0,
                QTableWidgetItem(receipt_date),
            )
            self.receipts_table.setItem(
                row,
                1,
                QTableWidgetItem(receipt.product_name),
            )
            self.receipts_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    receipt.supplier_name or "Ko'rsatilmagan"
                ),
            )
            self.receipts_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_quantity(receipt.quantity)
                ),
            )