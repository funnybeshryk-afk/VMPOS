from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.sale_service import SaleService
from app.ui.refund_history_dialog import RefundHistoryDialog
from app.ui.return_dialog import ReturnDialog
from app.ui.sale_details_dialog import SaleDetailsDialog
from app.utils.formatters import format_money
from app.widgets.badge import badge_cell, resolve_sale_status
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton
from app.widgets.summary_card import SummaryCard


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.sales = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Hisobotlar")
        title.setObjectName("pageTitle")

        filter_layout = QHBoxLayout()

        date_label = QLabel("Sana:")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        # Bugungi sana. Avval calendarWidget().selectedDate() olinardi —
        # u yangi yaratilgan kalendarda 01.01.2000 qaytaradi (Windows'da
        # ham), natijada hisobot "2000-yil"ni ko'rsatib, bo'sh chiqardi.
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.load_sales)

        # Bu sahifadagi yagona qora PrimaryButton — filtrni
        # yangilaydi, eng ko'p bosiladigan amal.
        self.refresh_button = PrimaryButton("Yangilash")
        self.refresh_button.clicked.connect(self.load_sales)

        self.return_button = SecondaryButton("Qaytarish")
        self.return_button.clicked.connect(self.open_return_dialog)

        self.refund_history_button = SecondaryButton(
            "Qaytarishlar tarixi"
        )
        self.refund_history_button.clicked.connect(
            self.open_refund_history
        )

        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.date_edit)
        filter_layout.addWidget(self.refresh_button)
        filter_layout.addWidget(self.return_button)
        filter_layout.addWidget(self.refund_history_button)
        filter_layout.addStretch()

        summary_layout = QHBoxLayout()

        self.sales_count_card = SummaryCard("Cheklar")
        self.today_total_card = SummaryCard("Savdo")
        self.cash_total_card = SummaryCard("Naqd pul")
        self.card_total_card = SummaryCard("Karta")

        summary_layout.addWidget(self.sales_count_card)
        summary_layout.addWidget(self.today_total_card)
        summary_layout.addWidget(self.cash_total_card)
        summary_layout.addWidget(self.card_total_card)

        self.sales_table = DataTable()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            "Chek raqami",
            "Sana",
            "Jami",
            "Holat",
        ])
        self.sales_table.pin_column_width(3)
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

        self.sales_count_card.set_value(summary["sales_count"])
        self.today_total_card.set_value(
            f"{format_money(summary['total_amount'])} so'm"
        )
        self.cash_total_card.set_value(
            f"{format_money(summary['cash_total'])} so'm"
        )
        self.card_total_card.set_value(
            f"{format_money(summary['card_total'])} so'm"
        )

        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            sale_date = sale.created_at.strftime("%d.%m.%Y %H:%M")

            status_text, status_variant = resolve_sale_status(
                sale.status
            )
            status_badge = badge_cell(status_text, status_variant)

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
                QTableWidgetItem(
                    f"{format_money(sale.total_amount)} so'm"
                ),
            )
            self.sales_table.setCellWidget(row, 3, status_badge)

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

    def open_return_dialog(self):
        dialog = ReturnDialog(parent=self)
        dialog.refundCompleted.connect(self.load_sales)
        dialog.exec()

        self.load_sales()

    def open_refund_history(self):
        dialog = RefundHistoryDialog(self)
        dialog.exec()