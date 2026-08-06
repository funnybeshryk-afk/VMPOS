from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
)

from app.services.supplier_service import SupplierService


class StockReceiptDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Tovar qabul qilish")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        product_name = QLabel(product.name)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem(
            "Yetkazib beruvchi tanlanmagan",
            None,
        )

        suppliers = SupplierService.get_all_suppliers()

        for supplier in suppliers:
            self.supplier_combo.addItem(
                supplier.name,
                supplier.id,
            )

        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setDecimals(3)
        self.quantity_spinbox.setMinimum(0.001)
        self.quantity_spinbox.setMaximum(999999)
        self.quantity_spinbox.setValue(1)

        if product.unit:
            self.quantity_spinbox.setSuffix(f" {product.unit}")

        layout.addRow("Mahsulot:", product_name)
        layout.addRow(
            "Yetkazib beruvchi:",
            self.supplier_combo,
        )
        layout.addRow("Kelgan miqdor:", self.quantity_spinbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_quantity(self):
        return self.quantity_spinbox.value()

    def get_supplier_id(self):
        return self.supplier_combo.currentData()