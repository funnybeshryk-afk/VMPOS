from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from app.utils.formatters import format_money, parse_number


class ShiftCloseDialog(QDialog):
    def __init__(self, shift, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Smenani yopish")
        self.setMinimumWidth(320)

        main_layout = QVBoxLayout(self)

        info_label = QLabel(
            f"Kassir: {shift.cashier_name}\n"
            f"Boshlang'ich summa: "
            f"{format_money(shift.opening_cash_amount)} so'm"
        )
        info_label.setObjectName("mutedText")

        form_layout = QFormLayout()

        self.closing_cash_edit = QLineEdit()
        self.closing_cash_edit.setPlaceholderText(
            "Kassadagi hisoblangan naqd pul"
        )

        form_layout.addRow(
            "Kassadagi naqd pul:", self.closing_cash_edit
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(info_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(buttons)

        self.closing_cash_edit.setFocus()

    def get_closing_cash_amount(self):
        try:
            return parse_number(self.closing_cash_edit.text())
        except ValueError:
            return 0
