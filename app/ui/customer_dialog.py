from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)


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

        self.debt_amount_spinbox = QDoubleSpinBox()
        self.debt_amount_spinbox.setDecimals(2)
        self.debt_amount_spinbox.setMinimum(0)
        self.debt_amount_spinbox.setMaximum(999999999)

        self.debt_date_edit = QDateEdit()
        self.debt_date_edit.setCalendarPopup(True)
        self.debt_date_edit.setDate(QDate.currentDate())

        if customer:
            self.name_edit.setText(customer.name or "")
            self.phone_edit.setText(customer.phone or "")
            self.address_edit.setText(customer.address or "")
            self.description_edit.setPlainText(
                customer.description or ""
            )
            self.debt_amount_spinbox.setValue(
                customer.debt_amount or 0
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
        layout.addRow("Qarz summasi:", self.debt_amount_spinbox)
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
            "debt_amount": self.debt_amount_spinbox.value(),
            "debt_date": self.debt_date_edit.date().toPython(),
        }