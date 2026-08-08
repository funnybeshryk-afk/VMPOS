from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.models.user import ROLE_LABELS


class UserPickerDialog(QDialog):
    """Parolsiz "hozir kim ishlayapti" tanlovi.

    Ilovada login/parol tizimi yo'q — bu tanlov haqiqiy xavfsizlik
    chegarasi emas, faqat menyuni rolga qarab moslashtirish va
    smena ochishda kassirni oldindan belgilash uchun qulaylik.
    """

    def __init__(self, users, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Foydalanuvchini tanlash")
        self.setMinimumWidth(320)

        main_layout = QVBoxLayout(self)

        info_label = QLabel("Hozir kim ishlayapti?")
        info_label.setObjectName("sectionTitle")

        self.users_list = QListWidget()

        for user in users:
            role_label = ROLE_LABELS.get(user.role, user.role)
            item = QListWidgetItem(
                f"{user.full_name} — {role_label}"
            )
            item.setData(Qt.UserRole, user)
            self.users_list.addItem(item)

        if self.users_list.count() > 0:
            self.users_list.setCurrentRow(0)

        self.users_list.itemDoubleClicked.connect(self.accept)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)

        main_layout.addWidget(info_label)
        main_layout.addWidget(self.users_list)
        main_layout.addWidget(buttons)

    def get_selected_user(self):
        item = self.users_list.currentItem()

        if item is None:
            return None

        return item.data(Qt.UserRole)
