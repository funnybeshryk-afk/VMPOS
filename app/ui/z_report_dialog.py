from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from app.utils.formatters import format_money
from app.widgets.secondary_button import SecondaryButton
from app.i18n import tr


class ZReportDialog(QDialog):
    def __init__(self, shift, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("Z-hisobot — smena #{0}").format(shift.id))
        self.setMinimumWidth(360)

        main_layout = QVBoxLayout(self)

        title = QLabel(tr("Z-hisobot — smena #{0}").format(shift.id))
        title.setObjectName("pageTitle")

        form_layout = QFormLayout()

        opened_text = shift.opened_at.strftime("%d.%m.%Y %H:%M")
        closed_text = (
            shift.closed_at.strftime("%d.%m.%Y %H:%M")
            if shift.closed_at
            else "—"
        )

        form_layout.addRow(tr("Kassir:"), QLabel(shift.cashier_name))
        form_layout.addRow(tr("Ochilgan:"), QLabel(opened_text))
        form_layout.addRow(tr("Yopilgan:"), QLabel(closed_text))
        form_layout.addRow(
            tr("Cheklar soni:"), QLabel(str(shift.sales_count))
        )
        form_layout.addRow(
            tr("Savdo summasi:"),
            QLabel(tr("{0} so'm").format(format_money(shift.total_amount))),
        )
        form_layout.addRow(
            tr("Naqd pul:"),
            QLabel(tr("{0} so'm").format(format_money(shift.cash_total))),
        )
        form_layout.addRow(
            tr("Karta:"),
            QLabel(tr("{0} so'm").format(format_money(shift.card_total))),
        )
        form_layout.addRow(
            tr("Boshlang'ich summa (kassa):"),
            QLabel(
                tr("{0} so'm").format(format_money(shift.opening_cash_amount))
            ),
        )
        form_layout.addRow(
            tr("Kutilgan summa (kassa):"),
            QLabel(
                tr("{0} so'm").format(format_money(shift.expected_cash_amount))
            ),
        )
        form_layout.addRow(
            tr("Hisoblangan summa (kassa):"),
            QLabel(
                tr("{0} so'm").format(format_money(shift.closing_cash_amount))
            ),
        )

        difference_label = QLabel(
            self._difference_text(shift.cash_difference)
        )
        difference_label.setObjectName(
            self._difference_object_name(shift.cash_difference)
        )

        form_layout.addRow(tr("Farq:"), difference_label)

        close_button = SecondaryButton(tr("Yopish"))
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(title)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(close_button)

    @staticmethod
    def _difference_text(difference):
        if difference is None:
            return "—"

        if difference < -0.01:
            return tr("Kamomad: {0} so'm").format(format_money(abs(difference)))

        if difference > 0.01:
            return tr("Ortiqcha: {0} so'm").format(format_money(difference))

        return tr("Kassa mos keldi")

    @staticmethod
    def _difference_object_name(difference):
        if difference is None:
            return "statValue"

        if difference < -0.01:
            return "statValueDanger"

        if difference > 0.01:
            return "statValueWarning"

        return "statValue"
