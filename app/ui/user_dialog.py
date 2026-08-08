from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)

from app.models.user import ROLE_ADMIN, ROLE_CASHIER, ROLE_LABELS


class UserDialog(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Foydalanuvchi")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        self.full_name_edit = QLineEdit()

        self.role_combo = QComboBox()
        self.role_combo.addItem(ROLE_LABELS[ROLE_ADMIN], ROLE_ADMIN)
        self.role_combo.addItem(
            ROLE_LABELS[ROLE_CASHIER], ROLE_CASHIER
        )

        selected_role = user.role if user else ROLE_CASHIER
        role_index = self.role_combo.findData(selected_role)

        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)

        if user:
            self.full_name_edit.setText(user.full_name or "")

        layout.addRow("F.I.Sh.:", self.full_name_edit)
        layout.addRow("Rol:", self.role_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self):
        return {
            "full_name": self.full_name_edit.text().strip(),
            "role": self.role_combo.currentData(),
        }
