from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from app.utils.formatters import format_money, parse_number
from app.i18n import tr


class DebtPaymentDialog(QDialog):
    def __init__(self, customer, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("Qarz to'lovi"))
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        customer_name = QLabel(customer.name)
        debt_amount = QLabel(
            tr("{0} so'm").format(format_money(customer.debt_amount))
        )

        self.amount_edit = QLineEdit()
        self.amount_edit.setText(
            format_money(customer.debt_amount)
        )
        self.amount_edit.setPlaceholderText(
            tr("Masalan: 150 000 yoki 150 000,50")
        )

        layout.addRow(tr("Mijoz:"), customer_name)
        layout.addRow(tr("Qarz:"), debt_amount)
        layout.addRow(tr("To'lov summasi:"), self.amount_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_amount(self):
        return parse_number(self.amount_edit.text())