from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.services.backup_service import BackupService
from app.services.product_service import ProductService
from app.services.receipt_service import ReceiptPrintError, ReceiptService
from app.services.settings_service import SettingsService
from app.ui.backup_restore_dialog import BackupRestoreDialog
from app.ui.receipt_preview_dialog import ReceiptPreviewDialog
from app.ui.scanner_test_dialog import ScannerTestDialog
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

        # Soliq rekvizitlari — fiskalizatsiyaga tayyorgarlik (hozircha
        # hech narsa soliq operatoriga yuborilmaydi).
        fiscal_title = QLabel("Soliq rekvizitlari")
        fiscal_title.setObjectName("sectionTitle")

        fiscal_form = QFormLayout()

        self.store_tin_edit = QLineEdit()
        self.store_tin_edit.setPlaceholderText("9 yoki 14 xona")
        self.store_legal_name_edit = QLineEdit()
        self.default_vat_edit = QLineEdit()
        self.default_vat_edit.setPlaceholderText("Masalan: 12 (QQS to'lovchisi bo'lmasa — 0)")

        fiscal_form.addRow("STIR:", self.store_tin_edit)
        fiscal_form.addRow("Yuridik nomi:", self.store_legal_name_edit)
        fiscal_form.addRow("Standart QQS, %:", self.default_vat_edit)

        self.fiscal_hint_label = QLabel()
        self.fiscal_hint_label.setObjectName("mutedText")
        self.fiscal_hint_label.setWordWrap(True)

        # Chek printeri (FISKAL emas): oddiy tizim printeri orqali
        # (termoprinter drayveri) yoki PDF.
        receipt_title = QLabel("Chek printeri")
        receipt_title.setObjectName("sectionTitle")

        receipt_form = QFormLayout()

        self.receipt_printer_combo = QComboBox()
        self.receipt_paper_combo = QComboBox()
        self.receipt_paper_combo.addItem("80 mm", "80")
        self.receipt_paper_combo.addItem("58 mm", "58")
        self.receipt_footer_edit = QLineEdit()
        self.receipt_footer_edit.setPlaceholderText("Masalan: Xaridingiz uchun rahmat!")
        self.receipt_auto_print_checkbox = QCheckBox(
            "Savdodan keyin chekni avtomatik chop etish"
        )
        self.receipt_barcode_checkbox = QCheckBox(
            "Chekda shtrix-kod (chek raqami) chiqarish"
        )

        receipt_form.addRow("Printer:", self.receipt_printer_combo)
        receipt_form.addRow("Qog'oz kengligi:", self.receipt_paper_combo)
        receipt_form.addRow("Pastki yozuv:", self.receipt_footer_edit)

        self.test_receipt_view_button = SecondaryButton("Sinov chekini ko'rish")
        self.test_receipt_view_button.clicked.connect(self.view_test_receipt)
        self.test_receipt_print_button = SecondaryButton("Sinov chekini chop etish")
        self.test_receipt_print_button.clicked.connect(self.print_test_receipt)

        receipt_buttons = QHBoxLayout()
        receipt_buttons.addWidget(self.test_receipt_view_button)
        receipt_buttons.addWidget(self.test_receipt_print_button)
        receipt_buttons.addStretch()

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

        # Skaner sinovi: skaner nima yuborayotganini ko'rsatadi.
        scanner_title = QLabel("Skaner")
        scanner_title.setObjectName("sectionTitle")

        self.scanner_test_button = SecondaryButton("Skaner sinovi")
        self.scanner_test_button.clicked.connect(
            lambda: ScannerTestDialog(self).exec()
        )

        scanner_row = QHBoxLayout()
        scanner_row.addWidget(self.scanner_test_button)
        scanner_row.addStretch()

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
        main_layout.addWidget(fiscal_title)
        main_layout.addLayout(fiscal_form)
        main_layout.addWidget(self.fiscal_hint_label)
        main_layout.addWidget(receipt_title)
        main_layout.addLayout(receipt_form)
        main_layout.addWidget(self.receipt_auto_print_checkbox)
        main_layout.addWidget(self.receipt_barcode_checkbox)
        main_layout.addLayout(receipt_buttons)
        main_layout.addWidget(self.save_button)
        main_layout.addWidget(backup_title)
        main_layout.addLayout(backup_row)
        main_layout.addWidget(scanner_title)
        main_layout.addLayout(scanner_row)
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

        fiscal = SettingsService.get_fiscal_settings()
        self.store_tin_edit.setText(fiscal["store_tin"])
        self.store_legal_name_edit.setText(fiscal["store_legal_name"])
        self.default_vat_edit.setText(f"{fiscal['default_vat_rate']:g}")
        self._refresh_fiscal_hint(fiscal)
        self._load_receipt_settings()

    def _load_receipt_settings(self):
        receipt = ReceiptService.get_settings()

        self.receipt_printer_combo.clear()
        self.receipt_printer_combo.addItem("Tizim standarti", "")

        names = ReceiptService.list_printers()

        for name in names:
            self.receipt_printer_combo.addItem(name, name)

        saved = receipt["printer"]

        if saved and saved not in names:
            # Saqlangan printer hozir ulanmagan — tanlov yo'qolmasin.
            self.receipt_printer_combo.addItem(f"{saved} (topilmadi)", saved)

        self.receipt_printer_combo.setCurrentIndex(
            max(0, self.receipt_printer_combo.findData(saved))
        )
        self.receipt_paper_combo.setCurrentIndex(
            max(0, self.receipt_paper_combo.findData(receipt["paper_mm"]))
        )
        self.receipt_footer_edit.setText(receipt["footer"])
        self.receipt_auto_print_checkbox.setChecked(receipt["auto_print"])
        self.receipt_barcode_checkbox.setChecked(receipt["show_barcode"])

    def _receipt_form_data(self):
        return {
            "printer": self.receipt_printer_combo.currentData() or "",
            "paper_mm": self.receipt_paper_combo.currentData(),
            "footer": self.receipt_footer_edit.text(),
            "auto_print": self.receipt_auto_print_checkbox.isChecked(),
            "show_barcode": self.receipt_barcode_checkbox.isChecked(),
        }

    def view_test_receipt(self):
        # Ko'rish uchun avval joriy tanlovlarni saqlaymiz (qog'oz kengligi
        # va yozuv ko'rinishga ta'sir qiladi).
        try:
            ReceiptService.save_settings(self._receipt_form_data())
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        ReceiptPreviewDialog(ReceiptService.build_sample(), self).exec()

    def print_test_receipt(self):
        try:
            ReceiptService.save_settings(self._receipt_form_data())
            ReceiptService.print_test()
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
        except ReceiptPrintError as error:
            QMessageBox.warning(self, "Chek chop etilmadi", str(error))

    def _refresh_fiscal_hint(self, fiscal):
        gaps = ProductService.get_fiscal_gaps()
        mode = (
            "o'chiq (soliq operatori hali ulanmagan)"
            if fiscal["fiscal_mode"] == SettingsService.FISCAL_MODE_OFF
            else fiscal["fiscal_mode"]
        )

        self.fiscal_hint_label.setText(
            f"Fiskalizatsiya: {mode}. "
            f"IKPU kodi yo'q: {gaps['missing_ikpu']} / {gaps['total']} "
            f"mahsulot, qadoq kodi yo'q: {gaps['missing_package']}."
        )

    def save_settings(self):
        store_name = self.store_name_edit.text().strip()

        if not store_name:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Do'kon nomini kiriting.",
            )
            return

        # Soliq rekvizitlari avval tekshiriladi: xato bo'lsa hech narsa
        # saqlanmaydi (yarim saqlash yo'q).
        try:
            SettingsService.save_fiscal_settings({
                "store_tin": self.store_tin_edit.text(),
                "store_legal_name": self.store_legal_name_edit.text(),
                "default_vat_rate": self.default_vat_edit.text(),
            })
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        try:
            ReceiptService.save_settings(self._receipt_form_data())
        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
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