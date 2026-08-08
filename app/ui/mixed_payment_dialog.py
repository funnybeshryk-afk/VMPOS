from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.utils.formatters import format_money, parse_number
from app.widgets.badge import StatusBadge, set_badge_variant

_TOLERANCE = 0.01


class MixedPaymentDialog(QDialog):
    """Naqd va karta o'rtasida bo'lingan to'lov.

    Ikkala summa ham qo'lda kiritiladi va ular jami chek summasiga
    aniq teng bo'lishi kerak — bu yerda qaytim tushunchasi yo'q,
    chunki karta orqali qaytim berib bo'lmaydi.
    """

    def __init__(self, total_amount, parent=None):
        super().__init__(parent)

        self.total_amount = total_amount

        self.setWindowTitle("Aralash to'lov")
        self.setMinimumWidth(340)

        main_layout = QVBoxLayout(self)

        total_label = QLabel(
            f"Jami: {format_money(total_amount)} so'm"
        )
        total_label.setObjectName("cartTotal")
        total_label.setAlignment(Qt.AlignCenter)

        form_layout = QFormLayout()

        self.cash_amount_edit = QLineEdit()
        self.cash_amount_edit.setPlaceholderText("Masalan: 10 000")
        self.cash_amount_edit.textChanged.connect(
            self.update_remaining_hint
        )

        self.card_amount_edit = QLineEdit()
        self.card_amount_edit.setPlaceholderText("Masalan: 5 000")
        self.card_amount_edit.textChanged.connect(
            self.update_remaining_hint
        )

        form_layout.addRow("Naqd pul summasi:", self.cash_amount_edit)
        form_layout.addRow("Karta summasi:", self.card_amount_edit)

        self.remaining_badge = StatusBadge("", "success")

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.try_accept)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(total_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(
            self.remaining_badge,
            alignment=Qt.AlignCenter,
        )
        main_layout.addWidget(buttons)

        # Boshlang'ich taklif: butun summa naqdda — kassir shundan
        # kartaga tushadigan qismini ajratib kiritadi.
        self.cash_amount_edit.setText(format_money(total_amount))
        self.card_amount_edit.setText(format_money(0))

    def _parse_amount(self, edit):
        try:
            return parse_number(edit.text())
        except ValueError:
            return 0

    def update_remaining_hint(self):
        cash_amount = self._parse_amount(self.cash_amount_edit)
        card_amount = self._parse_amount(self.card_amount_edit)
        remaining = self.total_amount - (cash_amount + card_amount)

        if abs(remaining) <= _TOLERANCE:
            set_badge_variant(
                self.remaining_badge,
                "Summalar jamga mos",
                "success",
            )
        elif remaining > 0:
            set_badge_variant(
                self.remaining_badge,
                f"Yetishmayapti: {format_money(remaining)} so'm",
                "warning",
            )
        else:
            set_badge_variant(
                self.remaining_badge,
                f"Ortiqcha: {format_money(-remaining)} so'm",
                "danger",
            )

    def try_accept(self):
        cash_amount = self._parse_amount(self.cash_amount_edit)
        card_amount = self._parse_amount(self.card_amount_edit)

        if cash_amount < 0 or card_amount < 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Summalar manfiy bo'lishi mumkin emas.",
            )
            return

        if (
            abs((cash_amount + card_amount) - self.total_amount)
            > _TOLERANCE
        ):
            QMessageBox.warning(
                self,
                "Diqqat",
                "Naqd va karta summalari jami chek summasiga "
                "teng bo'lishi kerak.",
            )
            return

        self.accept()

    def get_payment_data(self):
        return (
            self._parse_amount(self.cash_amount_edit),
            self._parse_amount(self.card_amount_edit),
        )
