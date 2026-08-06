from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
)

from app.utils.formatters import format_money


class WeightDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Og'irlikni kiriting")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        product_name = QLabel(product.name)
        price_label = QLabel(
            f"{format_money(product.sell_price)} so'm / kg"
        )

        self.weight_spinbox = QDoubleSpinBox()
        self.weight_spinbox.setDecimals(3)
        self.weight_spinbox.setMinimum(0.001)
        self.weight_spinbox.setMaximum(product.quantity)
        self.weight_spinbox.setSingleStep(0.1)
        self.weight_spinbox.setValue(1)
        self.weight_spinbox.setSuffix(" kg")

        layout.addRow("Mahsulot:", product_name)
        layout.addRow("Narxi:", price_label)
        layout.addRow("Og'irligi:", self.weight_spinbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_weight(self):
        return self.weight_spinbox.value()