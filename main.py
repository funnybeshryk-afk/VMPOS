import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.database.migrations import DatabaseTooNewError, prepare_database
from app.services.backup_service import BackupService
from app.utils.app_logging import get_log_path, setup_logging
from app.utils import motion
from app.utils.data_migration import migrate_legacy_data
from app.utils.paths import (
    get_app_base_dir,
    get_bundle_base_dir,
    get_data_dir,
    get_database_path,
)

logger = logging.getLogger(__name__)


def _offer_legacy_import(interactive=True):
    """O'rnatuvchi bilan birinchi marta o'rnatilgan, lekin avval dasturni
    boshqa papkada ishlatgan do'kon uchun: eski bazani o'zi topolmaydi
    (u yangi papkada emas), shuning uchun bir marta so'raymiz."""

    # --smoke-test (CI) interaktiv emas: modal savol dasturni abadiy
    # kutib qoldirardi.
    if (
        not interactive
        or not getattr(sys, "frozen", False)
        or get_database_path().exists()
    ):
        return

    answer = QMessageBox.question(
        None,
        "Eski ma'lumotlar",
        "Bu dasturni avval boshqa papkada ishlatganmisiz?\n\n"
        "Agar \"Ha\" desangiz, eski papkani tanlang (ichida vmpos.db "
        "bor papka) — barcha mahsulot va savdolar ko'chiriladi.\n"
        "Agar do'kon birinchi marta ishga tushirilayotgan bo'lsa — \"Yo'q\".",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )

    if answer != QMessageBox.Yes:
        return

    folder = QFileDialog.getExistingDirectory(
        None, "Eski dastur papkasini tanlang"
    )

    if not folder:
        return

    if not migrate_legacy_data(Path(folder), get_data_dir()):
        QMessageBox.warning(
            None,
            "Topilmadi",
            "Tanlangan papkada vmpos.db topilmadi. Yangi baza yaratiladi.",
        )


def _smoke_check():
    """Yig'ilgan dastur uchun o'z-o'zini tekshirish (CI'da `--smoke-test`).
    Qaytaradi: topilmagan resurslar ro'yxati (bo'sh = hammasi joyida)."""

    base = get_bundle_base_dir()
    required = [
        base / "assets" / "styles" / "style.qss",
        base / "assets" / "logo.png",
        base / "assets" / "logo.ico",
        base / "assets" / "logo_mark.png",
        base / "assets" / "icons" / "feather" / "shopping-cart.svg",
    ]

    return [str(path) for path in required if not path.is_file()]


def _prepare_data(app, interactive=True):
    """Ma'lumotlarni tayyorlaydi. Muvaffaqiyatli bo'lsa True; aks holda
    foydalanuvchiga tushunarli xabar ko'rsatib False qaytaradi (dastur
    bazaga TEGMAGAN holda yopiladi)."""

    try:
        # Eski versiyalar bazani .exe yonida saqlagan — birinchi
        # ishga tushishda yangi joyga o'zi ko'chadi.
        migrate_legacy_data(get_app_base_dir(), get_data_dir())
        _offer_legacy_import(interactive)

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
    smoke_test = "--smoke-test" in sys.argv

    setup_logging()

    app = QApplication(sys.argv)

    # Oyna/taskbar ikonkasi. Yig'ilgan .exe'da u PyInstaller --icon
    # bilan ham o'rnatilgan, lekin `python main.py` va portativ
    # ishga tushirishda ham to'g'ri chiqishi uchun kodda ham beramiz.
    app.setWindowIcon(
        QIcon(str(get_bundle_base_dir() / "assets" / "logo.ico"))
    )

    if smoke_test:
        missing = _smoke_check()

        if missing:
            logger.error("Resurslar topilmadi: %s", missing)
            print("SMOKE FAIL, topilmadi:", *missing, sep="\n  ")
            sys.exit(2)

    # CWD'ga emas — .exe sifatida yig'ilganda (ayniqsa --onefile)
    # CWD bu faylni topa olmaydi, chunki --add-data bilan qo'shilgan
    # resurslar sys._MEIPASS'ga chiqariladi, CWD'ga emas.
    style_path = get_bundle_base_dir() / "assets" / "styles" / "style.qss"

    with open(style_path, "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    if not _prepare_data(app, interactive=not smoke_test):
        sys.exit(1)

    # Animatsiyalar yoqilgan/o'chirilgani (Sozlamalar) — baza tayyor bo'lgach.
    motion.load_from_settings()

    # Oyna faqat baza tayyor bo'lgandan keyin import qilinadi: sahifalar
    # yaratilayotganda bazaga murojaat qiladi.
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    if smoke_test:
        # Oyna to'liq qurildi (baza, sahifalar, ikonkalar) — muvaffaqiyat.
        from app.utils.icons import load_icon

        if load_icon("shopping-cart").isNull():
            print("SMOKE FAIL: ikonka yuklanmadi")
            sys.exit(3)

        print("SMOKE OK")
        QTimer.singleShot(0, app.quit)
        sys.exit(app.exec())

    # Yangi versiyani fonda tekshirish: oyna ochilgandan 5 soniya
    # keyin, faqat o'rnatilgan dasturda; yangilanish bo'lsa taklif
    # chiqadi, aks holda hech narsa ko'rinmaydi.
    from app.services.update_service import can_install

    if can_install():
        QTimer.singleShot(
            5000,
            lambda: window.settings_page.update_flow.check(silent=True),
        )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
