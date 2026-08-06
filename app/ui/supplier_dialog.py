from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)


class SupplierDialog(QDialog):
    def __init__(self, supplier=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Yetkazib beruvchi")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.description_edit = QTextEdit()

        if supplier:
            self.name_edit.setText(supplier.name or "")
            self.phone_edit.setText(supplier.phone or "")
            self.address_edit.setText(supplier.address or "")
            self.description_edit.setPlainText(
                supplier.description or ""
            )

        layout.addRow("Nomi:", self.name_edit)
        layout.addRow("Telefon:", self.phone_edit)
        layout.addRow("Manzil:", self.address_edit)
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
        }