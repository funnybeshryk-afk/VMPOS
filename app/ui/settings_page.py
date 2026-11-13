from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.services.backup_service import BackupService
from app.services.settings_service import SettingsService
from app.ui.backup_restore_dialog import BackupRestoreDialog
from app.ui.update_flow import UpdateFlow
from app.utils import motion
from app.widgets.danger_button import DangerButton
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton
from app.version import APP_VERSION


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Sozlamalar")
        title.setObjectName("pageTitle")

        form_layout = QFormLayout()

        self.store_name_edit = QLineEdit()
        self.store_phone_edit = QLineEdit()
        self.store_address_edit = QLineEdit()

        form_layout.addRow("Do'kon nomi:", self.store_name_edit)
        form_layout.addRow("Telefon:", self.store_phone_edit)
        form_layout.addRow("Manzil:", self.store_address_edit)

        # Sahifadagi yagona amal — saqlash, shuning uchun yagona
        # qora PrimaryButton.
        self.save_button = PrimaryButton("Saqlash")
        self.save_button.clicked.connect(self.save_settings)

        backup_title = QLabel("Ma'lumotlar bazasi")
        backup_title.setObjectName("sectionTitle")

        # Yaratish — xavfsiz, qaytariladigan amal (SecondaryButton).
        # Tiklash esa joriy bazani butunlay almashtiradi — shuning
        # uchun DangerButton, xuddi boshqa qaytarib bo'lmaydigan
        # amallar kabi (masalan mahsulotni o'chirish).
        self.create_backup_button = SecondaryButton(
            "Zaxira nusxa yaratish"
        )
        self.create_backup_button.clicked.connect(
            self.create_backup
        )

        self.restore_backup_button = DangerButton(
            "Zaxiradan tiklash"
        )
        self.restore_backup_button.clicked.connect(
            self.open_restore_dialog
        )

        backup_row = QHBoxLayout()
        backup_row.addWidget(self.create_backup_button)
        backup_row.addWidget(self.restore_backup_button)
        backup_row.addStretch()

        interface_title = QLabel("Interfeys")
        interface_title.setObjectName("sectionTitle")

        # Qisqa animatsiyalar (jami summa, qator chiqishi, kartochka
        # "vspishka"si). Sekin kompyuterlarda o'chirib qo'yish mumkin —
        # natija o'zgarmaydi, faqat silliqlik yo'qoladi.
        self.animations_checkbox = QCheckBox(
            "Animatsiyalar (sekin kompyuterda o'chiring)"
        )
        self.animations_checkbox.setChecked(motion.is_enabled())
        self.animations_checkbox.toggled.connect(motion.save_enabled)

        update_title = QLabel("Dastur versiyasi")
        update_title.setObjectName("sectionTitle")

        version_label = QLabel(f"VMPOS v{APP_VERSION}")
        version_label.setObjectName("mutedText")

        self.check_update_button = SecondaryButton(
            "Yangilanishni tekshirish"
        )
        self.update_flow = UpdateFlow(self)
        self.check_update_button.clicked.connect(
            lambda: self.update_flow.check(silent=False)
        )

        # Internet cheklangan tarmoq uchun: o'rnatuvchini fayldan o'rnatish.
        self.install_file_button = SecondaryButton("Fayldan o'rnatish")
        self.install_file_button.clicked.connect(
            lambda: self.update_flow.install_from_file()
        )

        update_row = QHBoxLayout()
        update_row.addWidget(version_label)
        update_row.addWidget(self.check_update_button)
        update_row.addWidget(self.install_file_button)
        update_row.addStretch()

        main_layout.addWidget(title)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.save_button)
        main_layout.addWidget(backup_title)
        main_layout.addLayout(backup_row)
        main_layout.addWidget(interface_title)
        main_layout.addWidget(self.animations_checkbox)
        main_layout.addWidget(update_title)
        main_layout.addLayout(update_row)
        main_layout.addStretch()

        self.load_settings()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_settings()

    def load_settings(self):
        settings = SettingsService.get_store_settings()

        self.animations_checkbox.blockSignals(True)
        self.animations_checkbox.setChecked(motion.is_enabled())
        self.animations_checkbox.blockSignals(False)

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

    def create_backup(self):
        try:
            backup_path = BackupService.create_backup()

        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        except Exception:
            QMessageBox.critical(
                self,
                "Xatolik",
                "Zaxira nusxa yaratishda xatolik yuz berdi.",
            )
            return

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"Zaxira nusxa yaratildi: {backup_path.name}",
        )

    def open_restore_dialog(self):
        dialog = BackupRestoreDialog(self)
        dialog.exec()