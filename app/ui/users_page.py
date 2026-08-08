from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.user import ROLE_ADMIN
from app.services.user_service import UserService
from app.ui.user_dialog import UserDialog
from app.widgets.badge import badge_cell
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class UsersPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Foydalanuvchilar")
        title.setObjectName("pageTitle")

        buttons_layout = QHBoxLayout()

        self.add_button = PrimaryButton("Qo'shish")
        self.add_button.clicked.connect(self.add_user)

        self.edit_button = SecondaryButton("Tahrirlash")
        self.edit_button.clicked.connect(self.edit_user)

        self.delete_button = DangerButton("O'chirish")
        self.delete_button.clicked.connect(self.delete_user)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()

        self.users_table = DataTable()
        self.users_table.setColumnCount(2)
        self.users_table.setHorizontalHeaderLabels([
            "F.I.Sh.",
            "Rol",
        ])
        self.users_table.pin_column_width(1)

        main_layout.addWidget(title)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.users_table)

        self.load_users()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_users()

    def load_users(self):
        users = UserService.get_all_users()

        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            name_item = QTableWidgetItem(user.full_name)
            name_item.setData(Qt.UserRole, user.id)

            self.users_table.setItem(row, 0, name_item)

            if user.role == ROLE_ADMIN:
                role_badge = badge_cell("Administrator", "success")
            else:
                role_badge = badge_cell("Kassir", "neutral")

            self.users_table.setCellWidget(row, 1, role_badge)

    def get_selected_user_id(self):
        current_row = self.users_table.currentRow()

        if current_row < 0:
            return None

        item = self.users_table.item(current_row, 0)

        if item is None:
            return None

        return item.data(Qt.UserRole)

    def add_user(self):
        dialog = UserDialog(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        try:
            UserService.create_user(data)
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        self.load_users()

    def edit_user(self):
        user_id = self.get_selected_user_id()

        if user_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Tahrirlash uchun foydalanuvchini tanlang.",
            )
            return

        user = UserService.get_user(user_id)

        if user is None:
            return

        dialog = UserDialog(user, self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        try:
            UserService.update_user(user_id, data)
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        self.load_users()

    def delete_user(self):
        user_id = self.get_selected_user_id()

        if user_id is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "O'chirish uchun foydalanuvchini tanlang.",
            )
            return

        user = UserService.get_user(user_id)

        if user is None:
            return

        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            f'"{user.full_name}" o‘chirmoqchimisiz?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            UserService.delete_user(user_id)
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        self.load_users()
