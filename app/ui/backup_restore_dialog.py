from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.backup_service import BackupService
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.secondary_button import SecondaryButton


def _format_size(num_bytes):
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"

    return f"{num_bytes / 1024:.1f} KB"


class BackupRestoreDialog(QDialog):
    """backups/ papkasidagi zaxiralar ro'yxati + tiklash.

    Tiklash — joriy bazani butunlay almashtiradi, shuning uchun
    tasdiqlash so'raladi va (BackupService.restore_backup ichida)
    joriy holat ham avtomatik zaxiralanadi. Tiklashdan keyin
    dasturdagi barcha ochiq sahifalar/oynalar eski (endi noto'g'ri)
    ma'lumotni xotirada saqlab qolgan bo'lishi mumkin — shuning
    uchun tiklashdan so'ng dastur yopiladi, foydalanuvchi uni qayta
    ochishi kerak.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Zaxiradan tiklash")
        self.setMinimumWidth(480)
        self.resize(480, 380)

        main_layout = QVBoxLayout(self)

        self.backups_table = DataTable()
        self.backups_table.setColumnCount(2)
        self.backups_table.setHorizontalHeaderLabels([
            "Fayl",
            "Hajmi",
        ])
        self.backups_table.pin_column_width(1)
        self.backups_table.cellDoubleClicked.connect(
            self.restore_selected
        )

        self.restore_button = DangerButton(
            "Tanlangandan tiklash"
        )
        self.restore_button.clicked.connect(self.restore_selected)

        self.browse_button = SecondaryButton(
            "Boshqa faylni tanlash..."
        )
        self.browse_button.clicked.connect(self.restore_from_browse)

        close_button = SecondaryButton("Bekor qilish")
        close_button.clicked.connect(self.reject)

        main_layout.addWidget(self.backups_table)
        main_layout.addWidget(self.restore_button)
        main_layout.addWidget(self.browse_button)
        main_layout.addWidget(close_button)

        self.load_backups()

    def load_backups(self):
        self._backups = BackupService.get_backups()

        self.backups_table.setRowCount(len(self._backups))

        for row, backup_path in enumerate(self._backups):
            name_item = QTableWidgetItem(backup_path.name)
            name_item.setData(Qt.UserRole, str(backup_path))

            self.backups_table.setItem(row, 0, name_item)
            self.backups_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    _format_size(backup_path.stat().st_size)
                ),
            )

        if self._backups:
            self.backups_table.selectRow(0)

    def restore_selected(self):
        current_row = self.backups_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Tiklash uchun zaxira faylini tanlang.",
            )
            return

        item = self.backups_table.item(current_row, 0)
        self._confirm_and_restore(item.data(Qt.UserRole))

    def restore_from_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Zaxira faylini tanlash",
            "backups",
            "SQLite baza (*.db)",
        )

        if not file_path:
            return

        self._confirm_and_restore(file_path)

    def _confirm_and_restore(self, backup_path):
        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            "Joriy baza shu zaxira bilan butunlay almashtiriladi.\n"
            "Joriy holat ham avtomatik zaxiralanadi, lekin bu "
            "amalni bekor qilib bo'lmaydi.\n\n"
            "Davom etasizmi?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            BackupService.restore_backup(backup_path)

        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        except Exception:
            QMessageBox.critical(
                self,
                "Xatolik",
                "Zaxiradan tiklashda xatolik yuz berdi.",
            )
            return

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            "Baza tiklandi. Dastur hozir yopiladi — "
            "o'zgarishlar kuchga kirishi uchun uni qayta oching.",
        )

        QApplication.instance().quit()
