from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from app.utils.formatters import format_money
from app.widgets.secondary_button import SecondaryButton


class ZReportDialog(QDialog):
    def __init__(self, shift, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Z-hisobot — smena #{shift.id}")
        self.setMinimumWidth(360)

        main_layout = QVBoxLayout(self)

        title = QLabel(f"Z-hisobot — smena #{shift.id}")
        title.setObjectName("pageTitle")

        form_layout = QFormLayout()

        opened_text = shift.opened_at.strftime("%d.%m.%Y %H:%M")
        closed_text = (
            shift.closed_at.strftime("%d.%m.%Y %H:%M")
            if shift.closed_at
            else "—"
        )

        form_layout.addRow("Kassir:", QLabel(shift.cashier_name))
        form_layout.addRow("Ochilgan:", QLabel(opened_text))
        form_layout.addRow("Yopilgan:", QLabel(closed_text))
        form_layout.addRow(
            "Cheklar soni:", QLabel(str(shift.sales_count))
        )
        form_layout.addRow(
            "Savdo summasi:",
            QLabel(f"{format_money(shift.total_amount)} so'm"),
        )
        form_layout.addRow(
            "Naqd pul:",
            QLabel(f"{format_money(shift.cash_total)} so'm"),
        )
        form_layout.addRow(
            "Karta:",
            QLabel(f"{format_money(shift.card_total)} so'm"),
        )
        form_layout.addRow(
            "Boshlang'ich summa (kassa):",
            QLabel(
                f"{format_money(shift.opening_cash_amount)} so'm"
            ),
        )
        form_layout.addRow(
            "Kutilgan summa (kassa):",
            QLabel(
                f"{format_money(shift.expected_cash_amount)} so'm"
            ),
        )
        form_layout.addRow(
            "Hisoblangan summa (kassa):",
            QLabel(
                f"{format_money(shift.closing_cash_amount)} so'm"
            ),
        )

        difference_label = QLabel(
            self._difference_text(shift.cash_difference)
        )
        difference_label.setObjectName(
            self._difference_object_name(shift.cash_difference)
        )

        form_layout.addRow("Farq:", difference_label)

        close_button = SecondaryButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(title)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(close_button)

    @staticmethod
    def _difference_text(difference):
        if difference is None:
            return "—"

        if difference < -0.01:
            return f"Kamomad: {format_money(abs(difference))} so'm"

        if difference > 0.01:
            return f"Ortiqcha: {format_money(difference)} so'm"

        return "Kassa mos keldi"

    @staticmethod
    def _difference_object_name(difference):
        if difference is None:
            return "statValue"

        if difference < -0.01:
            return "statValueDanger"

        if difference > 0.01:
            return "statValueWarning"

        return "statValue"
