from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)

from app.utils.formatters import (
    format_money,
    format_quantity,
    parse_number,
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

        self.buy_price.setPlaceholderText("Masalan: 15 000,50")
        self.sell_price.setPlaceholderText("Masalan: 18 000")
        self.quantity.setPlaceholderText("Masalan: 10 yoki 0,5")
        self.min_quantity.setPlaceholderText("Masalan: 2")

        if product:
            self.barcode.setText(product.barcode or "")
            self.name.setText(product.name or "")
            self.category.setText(product.category or "")
            self.buy_price.setText(format_money(product.buy_price))
            self.sell_price.setText(format_money(product.sell_price))
            self.unit.setText(product.unit or "")
            self.quantity.setText(
                format_quantity(product.quantity)
            )
            self.min_quantity.setText(
                format_quantity(product.min_quantity)
            )
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
            "buy_price": parse_number(self.buy_price.text()),
            "sell_price": parse_number(self.sell_price.text()),
            "unit": self.unit.text(),
            "quantity": parse_number(self.quantity.text()),
            "min_quantity": parse_number(
                self.min_quantity.text()
            ),
            "description": self.description.toPlainText(),
        }