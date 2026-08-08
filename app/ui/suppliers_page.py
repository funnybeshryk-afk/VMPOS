from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.supplier_service import SupplierService
from app.ui.supplier_dialog import SupplierDialog
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class SuppliersPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Yetkazib beruvchilar")
        title.setObjectName("pageTitle")

        buttons_layout = QHBoxLayout()

        self.add_button = PrimaryButton("Qo'shish")
        self.add_button.clicked.connect(self.add_supplier)

        self.edit_button = SecondaryButton("Tahrirlash")
        self.edit_button.clicked.connect(self.edit_supplier)

        self.delete_button = DangerButton("O'chirish")
        self.delete_button.clicked.connect(self.delete_supplier)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()

        self.suppliers_table = DataTable()
        self.suppliers_table.setColumnCount(3)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Nomi",
            "Telefon",
            "Manzil",
        ])

        main_layout.addWidget(title)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.suppliers_table)

        self.load_suppliers()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_suppliers()

    def load_suppliers(self):
        suppliers = SupplierService.get_all_suppliers()

        self.suppliers_table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            name_item = QTableWidgetItem(supplier.name)
            name_item.setData(Qt.UserRole, supplier.id)

            self.suppliers_table.setItem(row, 0, name_item)
            self.suppliers_table.setItem(
                row,
                1,
                QTableWidgetItem(supplier.phone or ""),
            )
            self.suppliers_table.setItem(
                row,
                2,
                QTableWidgetItem(supplier.address or ""),
            )

    def get_selected_supplier_id(self):
        current_row = self.suppliers_table.currentRow()

        if current_row < 0:
            return None

        item = self.suppliers_table.item(current_row, 0)

        if item is None:
            return None

        return item.data(Qt.UserRole)

    def add_supplier(self):
        dialog = SupplierDialog(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        if not data["name"]:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Yetkazib beruvchi nomini kiriting.",
            )
            return

        SupplierService.create_supplier(data)
        self.load_suppliers()

    def edit_supplier(self):
        supplier_id = self.get_selected_supplier_id()

        if supplier_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Tahrirlash uchun yetkazib beruvchini tanlang.",
            )
            return

        supplier = SupplierService.get_supplier(supplier_id)

        if supplier is None:
            return

        dialog = SupplierDialog(supplier, self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        if not data["name"]:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Yetkazib beruvchi nomini kiriting.",
            )
            return

        SupplierService.update_supplier(supplier_id, data)
        self.load_suppliers()

    def delete_supplier(self):
        supplier_id = self.get_selected_supplier_id()

        if supplier_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "O'chirish uchun yetkazib beruvchini tanlang.",
            )
            return

        supplier = SupplierService.get_supplier(supplier_id)

        if supplier is None:
            return

        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            f'"{supplier.name}" o‘chirmoqchimisiz?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            SupplierService.delete_supplier(supplier_id)
            self.load_suppliers()