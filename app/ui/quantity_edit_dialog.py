from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
)

from app.utils.formatters import format_money, format_quantity


class QuantityEditDialog(QDialog):
    def __init__(self, product, current_quantity, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Miqdorni o'zgartirish")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        product_name = QLabel(product.name)
        price_label = QLabel(
            f"{format_money(product.sell_price)} so'm"
        )

        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setMinimum(0.001)
        self.quantity_spinbox.setMaximum(product.quantity)

        unit = (product.unit or "").strip().lower()

        if unit in {"kg", "кг"}:
            self.quantity_spinbox.setDecimals(3)
            self.quantity_spinbox.setSingleStep(0.1)
            self.quantity_spinbox.setSuffix(" kg")
        else:
            self.quantity_spinbox.setDecimals(0)
            self.quantity_spinbox.setMinimum(1)
            self.quantity_spinbox.setSingleStep(1)

        self.quantity_spinbox.setValue(current_quantity)

        layout.addRow("Mahsulot:", product_name)
        layout.addRow("Narxi:", price_label)
        layout.addRow("Miqdor:", self.quantity_spinbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_quantity(self):
        return self.quantity_spinbox.value()