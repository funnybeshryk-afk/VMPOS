from PySide6.QtWidgets import QDialog, QTableWidgetItem, QVBoxLayout

from app.services.refund_service import RefundService
from app.utils.formatters import format_money
from app.widgets.data_table import DataTable
from app.widgets.secondary_button import SecondaryButton
from app.i18n import tr


class RefundHistoryDialog(QDialog):
    """Barcha qaytarishlar tarixi — DebtPaymentsDialog bilan bir xil
    naqsh: ro'yxat + Yopish, faqat qaytarish operatsiyalari uchun.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("Qaytarishlar tarixi"))
        self.resize(650, 400)

        main_layout = QVBoxLayout(self)

        self.refunds_table = DataTable()
        self.refunds_table.setColumnCount(4)
        self.refunds_table.setHorizontalHeaderLabels([
            tr("Sana"),
            tr("Chek raqami"),
            tr("Kassir"),
            tr("Summa"),
        ])
        self.refunds_table.pin_column_width(1)

        close_button = SecondaryButton(tr("Yopish"))
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(self.refunds_table)
        main_layout.addWidget(close_button)

        self.load_refunds()

    def load_refunds(self):
        refunds = RefundService.get_refund_history()

        self.refunds_table.setRowCount(len(refunds))

        for row, refund in enumerate(refunds):
            refund_date = refund.created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

            self.refunds_table.setItem(
                row, 0, QTableWidgetItem(refund_date)
            )
            self.refunds_table.setItem(
                row, 1, QTableWidgetItem(f"#{refund.sale_id}")
            )
            self.refunds_table.setItem(
                row,
                2,
                QTableWidgetItem(refund.cashier_name or "—"),
            )
            self.refunds_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    tr("{0} so'm").format(format_money(refund.total_amount))
                ),
            )
