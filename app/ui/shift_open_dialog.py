from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from app.models.user import ROLE_LABELS
from app.utils.formatters import parse_number


class ShiftOpenDialog(QDialog):
    def __init__(self, users, parent=None, selected_user_id=None):
        super().__init__(parent)

        self.setWindowTitle("Smenani ochish")
        self.setMinimumWidth(320)

        main_layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.cashier_combo = QComboBox()

        selected_index = 0

        for index, user in enumerate(users):
            role_label = ROLE_LABELS.get(user.role, user.role)
            self.cashier_combo.addItem(
                f"{user.full_name} — {role_label}", user
            )

            if user.id == selected_user_id:
                selected_index = index

        self.cashier_combo.setCurrentIndex(selected_index)

        self.opening_cash_edit = QLineEdit()
        self.opening_cash_edit.setText("0")
        self.opening_cash_edit.setPlaceholderText(
            "Masalan: 100 000"
        )

        form_layout.addRow("Kassir:", self.cashier_combo)
        form_layout.addRow(
            "Boshlang'ich summa:", self.opening_cash_edit
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(buttons)

    def get_shift_data(self):
        user = self.cashier_combo.currentData()

        try:
            opening_cash_amount = parse_number(
                self.opening_cash_edit.text()
            )
        except ValueError:
            opening_cash_amount = 0

        if user is None:
            return "", opening_cash_amount, None

        return user.full_name, opening_cash_amount, user.id
