from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.sale_service import SaleService
from app.ui.sale_details_dialog import SaleDetailsDialog


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.sales = {}

        main_layout = QVBoxLayout(self)

        title = QLabel("Hisobotlar")
        title.setObjectName("pageTitle")

        filter_layout = QHBoxLayout()

        date_label = QLabel("Sana:")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(
            self.date_edit.calendarWidget().selectedDate()
        )
        self.date_edit.dateChanged.connect(self.load_sales)

        self.refresh_button = QPushButton("Yangilash")
        self.refresh_button.clicked.connect(self.load_sales)

        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.date_edit)
        filter_layout.addWidget(self.refresh_button)
        filter_layout.addStretch()

        summary_layout = QHBoxLayout()

        self.sales_count_label = QLabel("Cheklar: 0")
        self.today_total_label = QLabel("Savdo: 0 so'm")
        self.cash_total_label = QLabel("Naqd pul: 0 so'm")
        self.card_total_label = QLabel("Karta: 0 so'm")

        summary_layout.addWidget(self.sales_count_label)
        summary_layout.addWidget(self.today_total_label)
        summary_layout.addWidget(self.cash_total_label)
        summary_layout.addWidget(self.card_total_label)
        summary_layout.addStretch()

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            "Chek raqami",
            "Sana",
            "Jami",
            "Holat",
        ])

        self.sales_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.sales_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.sales_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.sales_table.cellDoubleClicked.connect(
            self.open_sale_details
        )

        main_layout.addWidget(title)
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(self.sales_table)

        self.load_sales()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_sales()

    def load_sales(self):
        selected_date = self.date_edit.date().toPython()

        sales = SaleService.get_sales_by_date(selected_date)
        summary = SaleService.get_summary_by_date(selected_date)

        self.sales = {sale.id: sale for sale in sales}

        self.sales_count_label.setText(
            f"Cheklar: {summary['sales_count']}"
        )
        self.today_total_label.setText(
            f"Savdo: {summary['total_amount']} so'm"
        )
        self.cash_total_label.setText(
            f"Naqd pul: {summary['cash_total']} so'm"
        )
        self.card_total_label.setText(
            f"Karta: {summary['card_total']} so'm"
        )

        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            sale_date = sale.created_at.strftime("%d.%m.%Y %H:%M")

            if sale.status == "refunded":
                status = "Qaytarilgan"
            else:
                status = "Yakunlangan"

            sale_id_item = QTableWidgetItem(str(sale.id))
            sale_id_item.setData(Qt.UserRole, sale.id)

            self.sales_table.setItem(row, 0, sale_id_item)
            self.sales_table.setItem(
                row,
                1,
                QTableWidgetItem(sale_date),
            )
            self.sales_table.setItem(
                row,
                2,
                QTableWidgetItem(f"{sale.total_amount} so'm"),
            )
            self.sales_table.setItem(
                row,
                3,
                QTableWidgetItem(status),
            )

    def open_sale_details(self, row, column):
        item = self.sales_table.item(row, 0)

        if item is None:
            return

        sale_id = item.data(Qt.UserRole)
        sale = self.sales.get(sale_id)

        if sale is None:
            return

        dialog = SaleDetailsDialog(sale, self)
        dialog.exec()

        self.load_sales()