from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.customer_service import CustomerService
from app.ui.customer_dialog import CustomerDialog
from app.ui.debt_payment_dialog import DebtPaymentDialog
from app.ui.debt_payments_dialog import DebtPaymentsDialog
from app.utils.formatters import format_money
from app.widgets.badge import badge_cell
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Mijozlar")
        title.setObjectName("pageTitle")

        buttons_layout = QHBoxLayout()

        # "Qo'shish" — ro'yxat sahifalarining barchasida (Mahsulotlar,
        # Yetkazib beruvchilar) bir xil qoidaga bo'ysunadi: eng ko'p
        # bosiladigan amal — yagona qora PrimaryButton.
        self.add_button = PrimaryButton("Qo'shish")
        self.add_button.clicked.connect(self.add_customer)

        self.edit_button = SecondaryButton("Tahrirlash")
        self.edit_button.clicked.connect(self.edit_customer)

        self.delete_button = DangerButton("O'chirish")
        self.delete_button.clicked.connect(self.delete_customer)

        self.debt_payment_button = SecondaryButton("Qarz to'lovi")
        self.debt_payment_button.clicked.connect(self.pay_debt)

        self.debt_history_button = SecondaryButton("To'lovlar tarixi")
        self.debt_history_button.clicked.connect(
            self.open_debt_payments_history
        )

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.debt_payment_button)
        buttons_layout.addWidget(self.debt_history_button)
        buttons_layout.addStretch()

        self.customers_table = DataTable()
        self.customers_table.setColumnCount(6)
        self.customers_table.setHorizontalHeaderLabels([
            "Nomi",
            "Telefon",
            "Manzil",
            "Qarz",
            "Qarz sanasi",
            "Holat",
        ])
        self.customers_table.pin_column_width(5)

        main_layout.addWidget(title)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.customers_table)

        self.load_customers()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_customers()

    def load_customers(self):
        customers = CustomerService.get_all_customers()

        self.customers_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            name_item = QTableWidgetItem(customer.name)
            name_item.setData(Qt.UserRole, customer.id)

            if customer.debt_amount > 0:
                debt_amount = (
                    f"{format_money(customer.debt_amount)} so'm"
                )

                if customer.debt_date:
                    debt_date = customer.debt_date.strftime(
                        "%d.%m.%Y"
                    )
                else:
                    debt_date = "-"
            else:
                debt_amount = "Yo'q"
                debt_date = "-"

            self.customers_table.setItem(row, 0, name_item)
            self.customers_table.setItem(
                row,
                1,
                QTableWidgetItem(customer.phone or ""),
            )
            self.customers_table.setItem(
                row,
                2,
                QTableWidgetItem(customer.address or ""),
            )
            self.customers_table.setItem(
                row,
                3,
                QTableWidgetItem(debt_amount),
            )
            self.customers_table.setItem(
                row,
                4,
                QTableWidgetItem(debt_date),
            )

            if customer.debt_amount > 0:
                status_badge = badge_cell("Qarz bor", "warning")
            else:
                status_badge = badge_cell("Qarz yo'q", "success")

            self.customers_table.setCellWidget(row, 5, status_badge)

    def get_selected_customer_id(self):
        current_row = self.customers_table.currentRow()

        if current_row < 0:
            return None

        item = self.customers_table.item(current_row, 0)

        if item is None:
            return None

        return item.data(Qt.UserRole)

    def add_customer(self):
        dialog = CustomerDialog(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        if not data["name"]:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mijoz nomini kiriting.",
            )
            return

        CustomerService.create_customer(data)
        self.load_customers()

    def edit_customer(self):
        customer_id = self.get_selected_customer_id()

        if customer_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Tahrirlash uchun mijozni tanlang.",
            )
            return

        customer = CustomerService.get_customer(customer_id)

        if customer is None:
            return

        dialog = CustomerDialog(customer, self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        if not data["name"]:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mijoz nomini kiriting.",
            )
            return

        CustomerService.update_customer(customer_id, data)
        self.load_customers()

    def delete_customer(self):
        customer_id = self.get_selected_customer_id()

        if customer_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "O'chirish uchun mijozni tanlang.",
            )
            return

        customer = CustomerService.get_customer(customer_id)

        if customer is None:
            return

        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            f'"{customer.name}" o‘chirmoqchimisiz?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            CustomerService.delete_customer(customer_id)
            self.load_customers()

    def pay_debt(self):
        customer_id = self.get_selected_customer_id()

        if customer_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "To'lov uchun mijozni tanlang.",
            )
            return

        customer = CustomerService.get_customer(customer_id)

        if customer is None:
            return

        if customer.debt_amount <= 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mijozda qarz yo'q.",
            )
            return

        dialog = DebtPaymentDialog(customer, self)

        if not dialog.exec():
            return

        try:
            updated_customer = CustomerService.pay_debt(
                customer_id,
                dialog.get_amount(),
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        self.load_customers()

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            "Qolgan qarz: "
            f"{format_money(updated_customer.debt_amount)} so'm",
        )

    def open_debt_payments_history(self):
        dialog = DebtPaymentsDialog(self)
        dialog.exec()