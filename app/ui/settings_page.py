from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.settings_service import SettingsService


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Sozlamalar")
        title.setObjectName("pageTitle")

        form_layout = QFormLayout()

        self.store_name_edit = QLineEdit()
        self.store_phone_edit = QLineEdit()
        self.store_address_edit = QLineEdit()

        form_layout.addRow("Do'kon nomi:", self.store_name_edit)
        form_layout.addRow("Telefon:", self.store_phone_edit)
        form_layout.addRow("Manzil:", self.store_address_edit)

        self.save_button = QPushButton("Saqlash")
        self.save_button.clicked.connect(self.save_settings)

        main_layout.addWidget(title)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.save_button)
        main_layout.addStretch()

        self.load_settings()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_settings()

    def load_settings(self):
        settings = SettingsService.get_store_settings()

        self.store_name_edit.setText(settings["store_name"])
        self.store_phone_edit.setText(settings["store_phone"])
        self.store_address_edit.setText(settings["store_address"])

    def save_settings(self):
        store_name = self.store_name_edit.text().strip()

        if not store_name:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Do'kon nomini kiriting.",
            )
            return

        SettingsService.save_store_settings({
            "store_name": store_name,
            "store_phone": self.store_phone_edit.text().strip(),
            "store_address": self.store_address_edit.text().strip(),
        })

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            "Sozlamalar saqlandi.",
        )