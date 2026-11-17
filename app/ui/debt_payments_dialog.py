from PySide6.QtWidgets import QDialog, QTableWidgetItem, QVBoxLayout

from app.services.customer_service import CustomerService
from app.utils.formatters import format_money
from app.widgets.data_table import DataTable
from app.widgets.secondary_button import SecondaryButton
from app.i18n import tr


class DebtPaymentsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("Qarz to'lovlari tarixi"))
        self.resize(650, 400)

        main_layout = QVBoxLayout(self)

        self.payments_table = DataTable()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels([
            tr("Sana"),
            tr("Mijoz"),
            tr("To'lov"),
        ])

        close_button = SecondaryButton(tr("Yopish"))
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(self.payments_table)
        main_layout.addWidget(close_button)

        self.load_payments()

    def load_payments(self):
        payments = CustomerService.get_debt_payments()

        self.payments_table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            payment_date = payment.created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

            self.payments_table.setItem(
                row,
                0,
                QTableWidgetItem(payment_date),
            )
            self.payments_table.setItem(
                row,
                1,
                QTableWidgetItem(payment.customer_name),
            )
            self.payments_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    tr("{0} so'm").format(format_money(payment.amount))
                ),
            )