from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.shift_service import ShiftService
from app.services.user_service import UserService
from app.state.session import get_current_user
from app.ui.shift_close_dialog import ShiftCloseDialog
from app.ui.shift_open_dialog import ShiftOpenDialog
from app.ui.z_report_dialog import ZReportDialog
from app.utils.formatters import format_money
from app.widgets.badge import badge_cell
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.success_button import SuccessButton
from app.widgets.summary_card import SummaryCard


class FinancePage(QWidget):
    def __init__(self):
        super().__init__()

        self.shifts = {}
        self.current_shift = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Moliya")
        title.setObjectName("pageTitle")

        # Joriy smena paneli — kassir va ochiq smenaning joriy tushumi
        # shu yerda ko'rinadi, sahifa har safar ochilganda yangilanadi.
        self.shift_panel = QFrame()
        self.shift_panel.setObjectName("panel")

        shift_panel_layout = QVBoxLayout(self.shift_panel)
        shift_panel_layout.setContentsMargins(16, 16, 16, 16)
        shift_panel_layout.setSpacing(12)

        shift_header_layout = QHBoxLayout()

        self.shift_status_label = QLabel()
        self.shift_status_label.setObjectName("sectionTitle")

        self.open_shift_button = PrimaryButton("Smenani ochish")
        self.open_shift_button.clicked.connect(self.open_shift)

        # Smenani yopish — kassadagi pulni sanab, tasdiqlash degani,
        # xuddi Sotuv sahifasidagi to'lov tugmasi kabi — shuning uchun
        # yagona yashil SuccessButton shu yerda ham qo'llanadi.
        self.close_shift_button = SuccessButton("Smenani yopish")
        self.close_shift_button.clicked.connect(self.close_shift)

        shift_header_layout.addWidget(self.shift_status_label)
        shift_header_layout.addStretch()
        shift_header_layout.addWidget(self.open_shift_button)
        shift_header_layout.addWidget(self.close_shift_button)

        shift_summary_layout = QHBoxLayout()

        self.sales_count_card = SummaryCard("Cheklar")
        self.total_amount_card = SummaryCard("Savdo")
        self.cash_total_card = SummaryCard("Naqd pul")
        self.card_total_card = SummaryCard("Karta")

        shift_summary_layout.addWidget(self.sales_count_card)
        shift_summary_layout.addWidget(self.total_amount_card)
        shift_summary_layout.addWidget(self.cash_total_card)
        shift_summary_layout.addWidget(self.card_total_card)

        shift_panel_layout.addLayout(shift_header_layout)
        shift_panel_layout.addLayout(shift_summary_layout)

        history_title = QLabel("Smenalar tarixi")
        history_title.setObjectName("sectionTitle")

        self.shifts_table = DataTable()
        self.shifts_table.setColumnCount(7)
        self.shifts_table.setHorizontalHeaderLabels([
            "Ochilgan",
            "Yopilgan",
            "Kassir",
            "Cheklar",
            "Savdo summasi",
            "Farq",
            "Holat",
        ])
        self.shifts_table.pin_column_width(6)
        self.shifts_table.cellDoubleClicked.connect(
            self.open_z_report
        )

        main_layout.addWidget(title)
        main_layout.addWidget(self.shift_panel)
        main_layout.addWidget(history_title)
        main_layout.addWidget(self.shifts_table)

        self.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()

    def load_data(self):
        self.current_shift = ShiftService.get_open_shift()
        self.update_shift_panel()

        shifts = ShiftService.get_all_shifts()
        self.shifts = {shift.id: shift for shift in shifts}

        self.shifts_table.setRowCount(len(shifts))

        for row, shift in enumerate(shifts):
            opened_text = shift.opened_at.strftime("%d.%m.%Y %H:%M")
            closed_text = (
                shift.closed_at.strftime("%d.%m.%Y %H:%M")
                if shift.closed_at
                else "—"
            )

            if shift.status == "open":
                status_badge = badge_cell("Ochiq", "success")
                sales_count_text = "—"
                total_amount_text = "—"
                difference_text = "—"
            else:
                status_badge = badge_cell("Yopiq", "neutral")
                sales_count_text = str(shift.sales_count)
                total_amount_text = (
                    f"{format_money(shift.total_amount)} so'm"
                )
                difference_text = self._format_difference(
                    shift.cash_difference
                )

            opened_item = QTableWidgetItem(opened_text)
            opened_item.setData(Qt.UserRole, shift.id)

            self.shifts_table.setItem(row, 0, opened_item)
            self.shifts_table.setItem(
                row, 1, QTableWidgetItem(closed_text)
            )
            self.shifts_table.setItem(
                row, 2, QTableWidgetItem(shift.cashier_name)
            )
            self.shifts_table.setItem(
                row, 3, QTableWidgetItem(sales_count_text)
            )
            self.shifts_table.setItem(
                row, 4, QTableWidgetItem(total_amount_text)
            )
            self.shifts_table.setItem(
                row, 5, QTableWidgetItem(difference_text)
            )
            self.shifts_table.setCellWidget(row, 6, status_badge)

    def update_shift_panel(self):
        if self.current_shift is None:
            self.shift_status_label.setText("Smena ochilmagan")
            self.open_shift_button.setVisible(True)
            self.close_shift_button.setVisible(False)

            self.sales_count_card.set_value("—")
            self.total_amount_card.set_value("—")
            self.cash_total_card.set_value("—")
            self.card_total_card.set_value("—")

            return

        opened_text = self.current_shift.opened_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        self.shift_status_label.setText(
            f"Smena ochiq — {self.current_shift.cashier_name} "
            f"({opened_text})"
        )
        self.open_shift_button.setVisible(False)
        self.close_shift_button.setVisible(True)

        summary = ShiftService.get_shift_preview(self.current_shift)

        self.sales_count_card.set_value(summary["sales_count"])
        self.total_amount_card.set_value(
            f"{format_money(summary['total_amount'])} so'm"
        )
        self.cash_total_card.set_value(
            f"{format_money(summary['cash_total'])} so'm"
        )
        self.card_total_card.set_value(
            f"{format_money(summary['card_total'])} so'm"
        )

    def open_shift(self):
        users = UserService.get_all_users()

        if not users:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Avval \"Foydalanuvchilar\" bo'limida xodim "
                "qo'shing.",
            )
            return

        current_user = get_current_user()
        selected_user_id = (
            current_user.id if current_user else None
        )

        dialog = ShiftOpenDialog(
            users, self, selected_user_id=selected_user_id
        )

        if not dialog.exec():
            return

        cashier_name, opening_cash_amount, cashier_user_id = (
            dialog.get_shift_data()
        )

        try:
            ShiftService.open_shift(
                cashier_name, opening_cash_amount, cashier_user_id
            )
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        self.load_data()

    def close_shift(self):
        if self.current_shift is None:
            return

        dialog = ShiftCloseDialog(self.current_shift, self)

        if not dialog.exec():
            return

        closing_cash_amount = dialog.get_closing_cash_amount()

        try:
            closed_shift = ShiftService.close_shift(
                self.current_shift.id, closing_cash_amount
            )
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        self.load_data()

        report_dialog = ZReportDialog(closed_shift, self)
        report_dialog.exec()

    def open_z_report(self, row, column):
        item = self.shifts_table.item(row, 0)

        if item is None:
            return

        shift_id = item.data(Qt.UserRole)
        shift = self.shifts.get(shift_id)

        if shift is None:
            return

        if shift.status != "closed":
            QMessageBox.information(
                self,
                "Diqqat",
                "Bu smena hali yopilmagan.",
            )
            return

        dialog = ZReportDialog(shift, self)
        dialog.exec()

    @staticmethod
    def _format_difference(difference):
        if difference is None:
            return "—"

        if difference < -0.01:
            return f"-{format_money(abs(difference))}"

        if difference > 0.01:
            return f"+{format_money(difference)}"

        return "0"
