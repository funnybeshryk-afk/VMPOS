from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.customer_service import CustomerService


class DebtPaymentsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Qarz to'lovlari tarixi")
        self.resize(650, 400)

        main_layout = QVBoxLayout(self)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels([
            "Sana",
            "Mijoz",
            "To'lov",
        ])

        self.payments_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.payments_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.payments_table.verticalHeader().setVisible(False)
        self.payments_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        close_button = QPushButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(self.payments_table)
        main_layout.addWidget(close_button)

        self.load_payments()

    def load_payments(self):
        payments = CustomerService.get_debt_payments()

        self.payments_table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            payment_date = payment.created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

            self.payments_table.setItem(
                row,
                0,
                QTableWidgetItem(payment_date),
            )
            self.payments_table.setItem(
                row,
                1,
                QTableWidgetItem(payment.customer_name),
            )
            self.payments_table.setItem(
                row,
                2,
                QTableWidgetItem(f"{payment.amount} so'm"),
            )