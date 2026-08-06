from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
)


class DebtPaymentDialog(QDialog):
    def __init__(self, customer, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Qarz to'lovi")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        customer_name = QLabel(customer.name)
        debt_amount = QLabel(f"{customer.debt_amount} so'm")

        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setMinimum(0.01)
        self.amount_spinbox.setMaximum(customer.debt_amount)
        self.amount_spinbox.setValue(customer.debt_amount)

        layout.addRow("Mijoz:", customer_name)
        layout.addRow("Qarz:", debt_amount)
        layout.addRow("To'lov summasi:", self.amount_spinbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_amount(self):
        return self.amount_spinbox.value()