"""Yangilanish oqimi (UI): tekshirish -> so'rash -> yuklash -> o'rnatish.

Tarmoq ishlari alohida oqimlarda (QThread) — kassa oynasi qotib
qolmaydi. Dasturni faqat foydalanuvchi "Yangilash"ni bosganda
yopamiz: savdo o'rtasida kutilmaganda yopilish hech qachon bo'lmaydi.
"""

import logging

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QProgressDialog,
)

from app.services import update_service
from app.services.backup_service import KIND_PREUPDATE, BackupService
from app.services.update_service import UpdateCancelled, UpdateError
from app.version import APP_VERSION

logger = logging.getLogger(__name__)


class _CheckWorker(QThread):
    found = Signal(object)  # UpdateInfo | None
    failed = Signal(str, str)  # tushunarli sabab, texnik tafsilot

    def run(self):
        try:
            self.found.emit(update_service.check_for_update())
        except UpdateError as error:
            self.failed.emit(str(error), error.technical)
        except Exception as error:  # kutilmagan xato ham oqimni o'ldirmasin
            logger.exception("Yangilanishni tekshirishda xato")
            self.failed.emit("Yangilanishni tekshirib bo'lmadi.", repr(error))


class _DownloadWorker(QThread):
    progress = Signal(int, int)
    done = Signal(object)  # Path
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._info = info
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            path = update_service.download_installer(
                self._info,
                progress=lambda got, total: self.progress.emit(got, total),
                is_cancelled=lambda: self._cancel,
            )
        except UpdateCancelled:
            self.cancelled.emit()
        except UpdateError as error:
            self.failed.emit(str(error))
        except Exception as error:
            logger.exception("Yuklab olishda xato")
            self.failed.emit(str(error))
        else:
            self.done.emit(path)


class UpdateFlow(QObject):
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._check_worker = None
        self._download_worker = None
        self._progress_dialog = None
        self._busy = False

    def _dialog_parent(self):
        # Sahifa yashirin bo'lishi mumkin — dialoglar faol oynada chiqsin.
        return QApplication.activeWindow() or self._parent

    # ---- tekshirish ----------------------------------------------

    def check(self, silent):
        """silent=True — dastur ochilganda: faqat yangilanish BOR bo'lsa
        ko'rinadi, xato/yo'q bo'lsa jim. False — tugma bosilganda:
        har bir natija haqida xabar beradi."""

        if self._busy:
            return

        self._busy = True
        self._silent = silent

        worker = _CheckWorker(self)
        worker.found.connect(self._on_found)
        worker.failed.connect(self._on_check_failed)
        worker.finished.connect(worker.deleteLater)
        self._check_worker = worker
        worker.start()

    def _on_check_failed(self, message, technical):
        self._busy = False
        logger.warning("Yangilanishni tekshirib bo'lmadi: %s | %s", message, technical)

        if self._silent:
            return

        box = QMessageBox(self._dialog_parent())
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Yangilanish")
        box.setText(message)
        box.setInformativeText(
            "Bu kompyuterda internet cheklangan bo'lsa: boshqa kompyuterdan "
            "yangilanish faylini (VMPOS-Setup-X.Y.Z.exe va .sha256) yuklab "
            "olib, \"Fayldan o'rnatish\" tugmasi orqali o'rnating."
        )
        box.setDetailedText(technical)
        box.exec()

    def _on_found(self, info):
        self._busy = False

        if info is None:
            if not self._silent:
                QMessageBox.information(
                    self._dialog_parent(),
                    "Yangilanish",
                    f"Sizda eng so'nggi versiya o'rnatilgan (v{APP_VERSION}).",
                )
            return

        self._offer(info)

    # ---- fayldan o'rnatish (internetsiz) -----------------------------

    def install_from_file(self):
        """Internet cheklangan tarmoq uchun: o'rnatuvchi (va .sha256) boshqa
        kompyuterdan/flesh-diskdan olinadi. Hash tekshiruvi majburiy."""

        parent = self._dialog_parent()

        if not update_service.can_install():
            QMessageBox.information(
                parent,
                "Yangilanish",
                "Fayldan o'rnatish faqat o'rnatilgan dasturda (Windows) ishlaydi.",
            )
            return

        path, _filter = QFileDialog.getOpenFileName(
            parent,
            "Yangilanish faylini tanlang",
            "",
            "VMPOS o'rnatuvchi (VMPOS-Setup-*.exe)",
        )

        if not path:
            return

        try:
            info = update_service.verify_local_installer(path)
        except UpdateError as error:
            QMessageBox.warning(parent, "Yangilanish", str(error))
            return

        answer = QMessageBox.question(
            parent,
            "Yangilanish",
            f"VMPOS v{info.version} o'rnatiladi (hozir v{APP_VERSION}).\n\n"
            "Joriy savdoni yakunlang. Ma'lumotlaringiz saqlanadi va "
            "avtomatik zaxiralanadi.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self._on_downloaded(info.installer_url)

    # ---- taklif --------------------------------------------------

    def _offer(self, info):
        box = QMessageBox(self._dialog_parent())
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Yangi versiya")
        box.setText(
            f"VMPOS v{info.version} chiqdi (sizda v{APP_VERSION})."
        )

        if info.notes:
            box.setInformativeText(info.notes[:600])

        if not update_service.can_install():
            box.setStandardButtons(QMessageBox.Ok)
            box.setDetailedText(
                "Avtomatik yangilash faqat o'rnatilgan dasturda ishlaydi."
            )
            box.exec()
            return

        later = box.addButton("Keyinroq", QMessageBox.RejectRole)
        update = box.addButton("Yangilash", QMessageBox.AcceptRole)
        box.setDefaultButton(later)
        box.setDetailedText(
            "Yangilashdan oldin joriy savdoni yakunlang. Ma'lumotlaringiz "
            "saqlanadi va avtomatik zaxiralanadi."
        )
        box.exec()

        if box.clickedButton() is update:
            self._download(info)

    # ---- yuklash -------------------------------------------------

    def _download(self, info):
        dialog = QProgressDialog(
            f"v{info.version} yuklanmoqda…", "Bekor qilish", 0, 100,
            self._dialog_parent(),
        )
        dialog.setWindowTitle("Yangilanish")
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setValue(0)
        self._progress_dialog = dialog

        worker = _DownloadWorker(info, self)
        worker.progress.connect(self._on_progress)
        worker.done.connect(self._on_downloaded)
        worker.failed.connect(self._on_download_failed)
        worker.cancelled.connect(self._close_progress)
        worker.finished.connect(worker.deleteLater)
        dialog.canceled.connect(worker.cancel)
        self._download_worker = worker
        worker.start()

    def _on_progress(self, received, total):
        if self._progress_dialog is not None and total > 0:
            self._progress_dialog.setValue(min(99, received * 100 // total))

    def _close_progress(self):
        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog = None

    def _on_download_failed(self, message):
        self._close_progress()
        logger.warning("Yuklab olish muvaffaqiyatsiz: %s", message)
        QMessageBox.warning(
            self._dialog_parent(),
            "Yangilanish",
            f"Yangilab bo'lmadi:\n{message}\n\nDastur avvalgidek ishlayveradi.",
        )

    def _on_downloaded(self, installer_path):
        self._close_progress()

        # Yangilashdan oldin bazaning nusxasi — o'rnatuvchi dastur
        # fayllariga tegadi, ma'lumotlarga emas, lekin ehtiyot shart.
        try:
            BackupService.create_backup(KIND_PREUPDATE)
        except Exception:
            logger.exception("Yangilashdan oldingi zaxira olinmadi")

        try:
            update_service.launch_installer(installer_path)
        except Exception as error:
            logger.exception("O'rnatuvchini ishga tushirib bo'lmadi")
            QMessageBox.warning(
                self._dialog_parent(),
                "Yangilanish",
                f"O'rnatuvchini ishga tushirib bo'lmadi:\n{error}",
            )
            return

        logger.info("O'rnatuvchi ishga tushirildi, dastur yopilmoqda")
        QApplication.quit()
