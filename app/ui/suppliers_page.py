from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.supplier_service import SupplierService
from app.ui.supplier_dialog import SupplierDialog


class SuppliersPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Yetkazib beruvchilar")
        title.setObjectName("pageTitle")

        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Qo'shish")
        self.add_button.clicked.connect(self.add_supplier)

        self.edit_button = QPushButton("Tahrirlash")
        self.edit_button.clicked.connect(self.edit_supplier)

        self.delete_button = QPushButton("O'chirish")
        self.delete_button.clicked.connect(self.delete_supplier)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(3)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Nomi",
            "Telefon",
            "Manzil",
        ])

        self.suppliers_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.suppliers_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.suppliers_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.suppliers_table.verticalHeader().setVisible(False)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

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