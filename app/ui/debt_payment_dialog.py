from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from app.utils.formatters import format_money, parse_number


class DebtPaymentDialog(QDialog):
    def __init__(self, customer, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Qarz to'lovi")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        customer_name = QLabel(customer.name)
        debt_amount = QLabel(
            f"{format_money(customer.debt_amount)} so'm"
        )

        self.amount_edit = QLineEdit()
        self.amount_edit.setText(
            format_money(customer.debt_amount)
        )
        self.amount_edit.setPlaceholderText(
            "Masalan: 150 000 yoki 150 000,50"
        )

        layout.addRow("Mijoz:", customer_name)
        layout.addRow("Qarz:", debt_amount)
        layout.addRow("To'lov summasi:", self.amount_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_amount(self):
        return parse_number(self.amount_edit.text())