import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.database.migrations import DatabaseTooNewError, prepare_database
from app.services.backup_service import BackupService
from app.utils.app_logging import get_log_path, setup_logging
from app.utils.data_migration import migrate_legacy_data
from app.utils.paths import get_app_base_dir, get_bundle_base_dir, get_data_dir

logger = logging.getLogger(__name__)


def _prepare_data(app):
    """Ma'lumotlarni tayyorlaydi. Muvaffaqiyatli bo'lsa True; aks holda
    foydalanuvchiga tushunarli xabar ko'rsatib False qaytaradi (dastur
    bazaga TEGMAGAN holda yopiladi)."""

    try:
        # Eski versiyalar bazani .exe yonida saqlagan — birinchi
        # ishga tushishda yangi joyga o'zi ko'chadi.
        migrate_legacy_data(get_app_base_dir(), get_data_dir())

        prepare_database()

    except DatabaseTooNewError:
        logger.exception("Baza dasturdan yangiroq")
        QMessageBox.critical(
            None,
            "Dasturni yangilang",
            "Ma'lumotlar bazasi dasturning yangiroq versiyasida "
            "yaratilgan.\n\nIltimos, dasturni oxirgi versiyaga "
            "yangilang. Ma'lumotlaringizga tegilmadi.",
        )
        return False

    except Exception:
        logger.exception("Bazani tayyorlashda xato")
        QMessageBox.critical(
            None,
            "Bazani ochib bo'lmadi",
            "Ma'lumotlar bazasini tayyorlashda xatolik yuz berdi.\n"
            "Ma'lumotlaringiz saqlangan (zaxira nusxasi mavjud).\n\n"
            f"Log fayli:\n{get_log_path()}",
        )
        return False

    # Kunlik avto-zaxira. Xato bo'lsa dasturni to'xtatmaymiz —
    # faqat logga yozamiz.
    try:
        BackupService.create_auto_backup_if_due()
    except Exception:
        logger.exception("Avto-zaxira olinmadi")

    return True


def main():
    setup_logging()

    app = QApplication(sys.argv)

    # CWD'ga emas — .exe sifatida yig'ilganda (ayniqsa --onefile)
    # CWD bu faylni topa olmaydi, chunki --add-data bilan qo'shilgan
    # resurslar sys._MEIPASS'ga chiqariladi, CWD'ga emas.
    style_path = get_bundle_base_dir() / "assets" / "styles" / "style.qss"

    with open(style_path, "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    if not _prepare_data(app):
        sys.exit(1)

    # Oyna faqat baza tayyor bo'lgandan keyin import qilinadi: sahifalar
    # yaratilayotganda bazaga murojaat qiladi.
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
