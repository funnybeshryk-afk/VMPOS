from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from app.utils.formatters import format_money, parse_number


class PaymentDialog(QDialog):
    def __init__(self, total_amount, parent=None):
        super().__init__(parent)

        self.total_amount = total_amount

        self.setWindowTitle("To'lov")
        self.setMinimumWidth(320)

        main_layout = QVBoxLayout(self)

        total_label = QLabel(
            f"Jami: {format_money(total_amount)} so'm"
        )
        total_label.setStyleSheet(
            "font-size: 18px; font-weight: 700;"
        )

        form_layout = QFormLayout()

        self.cash_radio = QRadioButton("Naqd pul")
        self.card_radio = QRadioButton("Karta")
        self.cash_radio.setChecked(True)

        self.paid_amount_edit = QLineEdit()
        self.paid_amount_edit.setText(format_money(total_amount))
        self.paid_amount_edit.setValidator(
            QDoubleValidator(0, 999999999, 2)
        )

        form_layout.addRow("To'lov turi:", self.cash_radio)
        form_layout.addRow("", self.card_radio)
        form_layout.addRow(
            "Berilgan summa:",
            self.paid_amount_edit,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.cash_radio.toggled.connect(
            self.update_payment_fields
        )
        self.card_radio.toggled.connect(
            self.update_payment_fields
        )

        main_layout.addWidget(total_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(buttons)

    def update_payment_fields(self):
        is_card_payment = self.card_radio.isChecked()

        self.paid_amount_edit.setDisabled(is_card_payment)

        if is_card_payment:
            self.paid_amount_edit.setText(
                format_money(self.total_amount)
            )

    def get_payment_data(self):
        payment_method = "cash"

        if self.card_radio.isChecked():
            payment_method = "card"

        paid_amount = parse_number(self.paid_amount_edit.text())

        return payment_method, paid_amount