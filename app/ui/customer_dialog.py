from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)

from app.utils.formatters import format_money, parse_number


class CustomerDialog(QDialog):
    def __init__(self, customer=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Mijoz")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.description_edit = QTextEdit()

        self.debt_amount_edit = QLineEdit()
        self.debt_amount_edit.setText("0")
        self.debt_amount_edit.setPlaceholderText(
            "Masalan: 150 000 yoki 150 000,50"
        )

        self.debt_date_edit = QDateEdit()
        self.debt_date_edit.setCalendarPopup(True)
        self.debt_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.debt_date_edit.setDate(QDate.currentDate())

        if customer:
            self.name_edit.setText(customer.name or "")
            self.phone_edit.setText(customer.phone or "")
            self.address_edit.setText(customer.address or "")
            self.description_edit.setPlainText(
                customer.description or ""
            )
            self.debt_amount_edit.setText(
                format_money(customer.debt_amount)
            )

            if customer.debt_date:
                self.debt_date_edit.setDate(
                    QDate(
                        customer.debt_date.year,
                        customer.debt_date.month,
                        customer.debt_date.day,
                    )
                )

        layout.addRow("Nomi:", self.name_edit)
        layout.addRow("Telefon:", self.phone_edit)
        layout.addRow("Manzil:", self.address_edit)
        layout.addRow("Qarz summasi:", self.debt_amount_edit)
        layout.addRow("Qarz sanasi:", self.debt_date_edit)
        layout.addRow("Izoh:", self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "debt_amount": parse_number(
                self.debt_amount_edit.text()
            ),
            "debt_date": self.debt_date_edit.date().toPython(),
        }