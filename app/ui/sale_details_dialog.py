from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.sale_service import SaleService
from app.utils.formatters import format_money, format_quantity
from app.widgets.badge import StatusBadge
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.secondary_button import SecondaryButton


class SaleDetailsDialog(QDialog):
    def __init__(self, sale, parent=None):
        super().__init__(parent)

        self.sale = sale

        self.setWindowTitle(f"Chek #{sale.id}")
        self.resize(600, 450)

        main_layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()

        title = QLabel(f"Chek #{sale.id}")
        title.setObjectName("pageTitle")

        if sale.status == "refunded":
            self.status_badge = StatusBadge("Qaytarilgan", "danger")
        else:
            self.status_badge = StatusBadge("Yakunlangan", "success")

        header_layout.addWidget(title)
        header_layout.addWidget(self.status_badge)
        header_layout.addStretch()

        self.items_table = DataTable()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Soni",
            "Jami",
        ])

        total_label = QLabel(
            f"Jami: {format_money(sale.total_amount)} so'm"
        )
        total_label.setObjectName("cartTotal")

        # Qaytarish — sotuvni bekor qiladi va tovarni omborga
        # qaytaradi, orqaga qaytarib bo'lmaydi — shuning uchun DangerButton.
        self.refund_button = DangerButton("Chekni qaytarish")
        self.refund_button.clicked.connect(self.refund_sale)

        if sale.status == "refunded":
            self.refund_button.setDisabled(True)

        close_button = SecondaryButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.items_table)
        main_layout.addWidget(total_label)
        main_layout.addWidget(self.refund_button)
        main_layout.addWidget(close_button)

        self.load_sale_items(sale.id)

    def load_sale_items(self, sale_id):
        sale_items = SaleService.get_sale_items(sale_id)

        self.items_table.setRowCount(len(sale_items))

        for row, sale_item in enumerate(sale_items):
            self.items_table.setItem(
                row,
                0,
                QTableWidgetItem(sale_item.product_name),
            )
            self.items_table.setItem(
                row,
                1,
                QTableWidgetItem(format_money(sale_item.price)),
            )
            self.items_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    format_quantity(sale_item.quantity)
                ),
            )
            self.items_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_money(sale_item.line_total)
                ),
            )

    def refund_sale(self):
        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            "Bu chekni qaytarmoqchimisiz?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            SaleService.refund_sale(self.sale.id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        self.sale.status = "refunded"

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            "Chek qaytarildi. Mahsulotlar qoldiqqa qaytdi.",
        )

        self.accept()