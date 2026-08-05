from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDialogButtonBox,
)


class ProductDialog(QDialog):
    def __init__(self, product=None):
        super().__init__()

        self.setWindowTitle("Yangi mahsulot")
        self.resize(450, 500)

        layout = QFormLayout(self)

        self.barcode = QLineEdit()
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.buy_price = QLineEdit()
        self.sell_price = QLineEdit()
        self.unit = QLineEdit()
        self.quantity = QLineEdit()
        self.min_quantity = QLineEdit()
        self.description = QTextEdit()

        if product:
            self.barcode.setText(product.barcode or "")
            self.name.setText(product.name or "")
            self.category.setText(product.category or "")
            self.buy_price.setText(str(product.buy_price))
            self.sell_price.setText(str(product.sell_price))
            self.unit.setText(product.unit or "")
            self.quantity.setText(str(product.quantity))
            self.min_quantity.setText(str(product.min_quantity))
            self.description.setPlainText(product.description or "")

        layout.addRow("Shtrix kod", self.barcode)
        layout.addRow("Nomi", self.name)
        layout.addRow("Kategoriya", self.category)
        layout.addRow("Sotib olish narxi", self.buy_price)
        layout.addRow("Sotish narxi", self.sell_price)
        layout.addRow("Birlik", self.unit)
        layout.addRow("Qoldiq", self.quantity)
        layout.addRow("Minimal qoldiq", self.min_quantity)
        layout.addRow("Tavsif", self.description)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self):
        return {
            "barcode": self.barcode.text(),
            "name": self.name.text(),
            "category": self.category.text(),
            "buy_price": float(self.buy_price.text() or 0),
            "sell_price": float(self.sell_price.text() or 0),
            "unit": self.unit.text(),
            "quantity": float(self.quantity.text() or 0),
            "min_quantity": float(self.min_quantity.text() or 0),
            "description": self.description.toPlainText(),
        }    