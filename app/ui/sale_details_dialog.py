from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.sale_service import SaleService
from app.ui.return_dialog import ReturnDialog
from app.utils.formatters import format_money, format_quantity
from app.widgets.badge import (
    StatusBadge,
    resolve_sale_status,
    set_badge_variant,
)
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.secondary_button import SecondaryButton


class SaleDetailsDialog(QDialog):
    def __init__(self, sale, parent=None):
        super().__init__(parent)

        self.sale = sale

        self.setWindowTitle(f"Chek #{sale.id}")
        self.resize(650, 470)

        main_layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()

        self.title_label = QLabel(f"Chek #{sale.id}")
        self.title_label.setObjectName("pageTitle")

        self.status_badge = StatusBadge("", "neutral")

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_badge)
        header_layout.addStretch()

        self.items_table = DataTable()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Soni",
            "Jami",
            "Qaytarilgan",
            "Qoldiq",
        ])

        self.total_label = QLabel()
        self.total_label.setObjectName("cartTotal")

        # Qaytarish — omborga tovar qaytadi va chekning moliyaviy
        # summasi kamayadi, orqaga qaytarib bo'lmaydi — shuning uchun
        # DangerButton. To'liq/qisman tanlov endi ReturnDialog ichida.
        self.refund_button = DangerButton("Qaytarish")
        self.refund_button.clicked.connect(self.open_return_dialog)

        close_button = SecondaryButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.items_table)
        main_layout.addWidget(self.total_label)
        main_layout.addWidget(self.refund_button)
        main_layout.addWidget(close_button)

        self.refresh_sale(sale)

    def refresh_sale(self, sale):
        self.sale = sale

        status_text, status_variant = resolve_sale_status(sale.status)
        set_badge_variant(self.status_badge, status_text, status_variant)

        self.total_label.setText(
            f"Jami: {format_money(sale.total_amount)} so'm"
        )

        self.refund_button.setDisabled(sale.status == "refunded")

        self.load_sale_items(sale.id)

    def load_sale_items(self, sale_id):
        sale_items = SaleService.get_sale_items(sale_id)

        self.items_table.setRowCount(len(sale_items))

        for row, sale_item in enumerate(sale_items):
            remaining = max(
                0, sale_item.quantity - sale_item.returned_quantity
            )

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
            self.items_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    format_quantity(sale_item.returned_quantity)
                ),
            )
            self.items_table.setItem(
                row,
                5,
                QTableWidgetItem(format_quantity(remaining)),
            )

    def open_return_dialog(self):
        dialog = ReturnDialog(sale=self.sale, parent=self)
        dialog.exec()

        updated_sale = SaleService.get_sale(self.sale.id)

        if updated_sale is not None:
            self.refresh_sale(updated_sale)
