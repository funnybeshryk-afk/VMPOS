import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app.database.database import DATABASE_PATH, engine
from app.utils.paths import get_backup_dir
from app.version import SCHEMA_VERSION

logger = logging.getLogger(__name__)

# DATABASE_PATH bilan bitta manba — yo'l shu yerda qayta yozilmaydi,
# aks holda ikkalasi kelajakda bir-biridan ajralib qolishi mumkin.
_DB_PATH = DATABASE_PATH

# Zaxira turlari (fayl nomidagi prefiks). "manual" — foydalanuvchi
# o'zi bosgan (eski nom formati o'zgarmagan: vmpos_<vaqt>.db), qolganlari
# avtomatik va ular soni cheklanadi (eng eskilari o'chiriladi).
KIND_MANUAL = "manual"
KIND_AUTO = "auto"
KIND_PREMIGRATE = "premigrate"

# Har tur uchun nechta nusxa saqlanadi. Qo'lda olinganlar hech qachon
# avtomatik o'chirilmaydi.
_KEEP_BY_KIND = {
    KIND_AUTO: 30,
    KIND_PREMIGRATE: 10,
}

# Avto-zaxira "kunlik": oxirgisidan shuncha soat o'tmagan bo'lsa, qayta
# olinmaydi (dastur kuniga bir necha marta ochilishi mumkin).
AUTO_BACKUP_INTERVAL_HOURS = 20

# Qo'shimcha nusxa (bulut bilan sinxronlanadigan papka — OneDrive,
# Google Drive, USB) — SettingsService'dagi shu kalit bo'yicha.
MIRROR_SETTING_KEY = "backup_mirror_dir"


def _backup_dir():
    # Har safar qayta hisoblanadi (modul import paytida emas) — shunda
    # ma'lumotlar papkasi testlarda/qayta sozlashda almashtirilishi mumkin.
    return get_backup_dir()


def _file_prefix(kind):
    return "vmpos_" if kind == KIND_MANUAL else f"vmpos_{kind}_"


class BackupService:

    @staticmethod
    def create_backup(kind=KIND_MANUAL):
        """Joriy bazadan xavfsiz nusxa — sqlite3'ning backup API'si
        orqali (oddiy fayl nusxalash emas).

        Dastur ochiq turgan paytda ham (masalan boshqa joyda
        tranzaksiya ketayotgan bo'lsa ham) izchil, buzilmagan nusxa
        kafolatlanadi — bu SQLite'ni "jonli" zaxiralashning rasmiy
        tavsiya etilgan usuli.
        """

        if not _DB_PATH.exists():
            raise ValueError("Baza fayli topilmadi.")

        backup_dir = _backup_dir()
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Mikrosekund aniqligi — soniya aniqligi restore_backup()
        # ichidagi avtomatik xavfsizlik nusxasi kabi tez ketma-ket
        # chaqiruvlarda to'qnashib, oldingi zaxirani jimgina ustidan
        # yozib yuborishi mumkin edi. Shu bilan birga, nomi band
        # bo'lib qolgan taqdirda ham hech qachon mavjud faylni
        # bosib o'tirmaydi — o'rniga keyingi bo'sh nomga yoziladi.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        prefix = _file_prefix(kind)
        backup_path = backup_dir / f"{prefix}{timestamp}.db"

        suffix = 1
        while backup_path.exists():
            backup_path = backup_dir / f"{prefix}{timestamp}_{suffix}.db"
            suffix += 1

        source = sqlite3.connect(str(_DB_PATH))

        try:
            destination = sqlite3.connect(str(backup_path))

            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()

        if kind != KIND_MANUAL:
            BackupService._prune(kind)
            BackupService._mirror(backup_path)

        return backup_path

    @staticmethod
    def create_auto_backup_if_due():
        """Dastur ochilganda chaqiriladi: oxirgi avto-zaxiradan
        AUTO_BACKUP_INTERVAL_HOURS soat o'tgan bo'lsa (yoki umuman
        bo'lmasa) yangisini oladi. Qaytaradi: yangi fayl yo'li yoki None."""

        if not _DB_PATH.exists():
            return None

        existing = BackupService._list_by_kind(KIND_AUTO)

        if existing:
            age_hours = (
                datetime.now().timestamp() - existing[0].stat().st_mtime
            ) / 3600

            if age_hours < AUTO_BACKUP_INTERVAL_HOURS:
                return None

        return BackupService.create_backup(KIND_AUTO)

    @staticmethod
    def get_backups():
        """Mavjud zaxira fayllari, eng yangisi birinchi."""

        backup_dir = _backup_dir()

        if not backup_dir.exists():
            return []

        return sorted(
            backup_dir.glob("vmpos_*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    @staticmethod
    def _list_by_kind(kind):
        backup_dir = _backup_dir()

        if not backup_dir.exists():
            return []

        return sorted(
            backup_dir.glob(f"{_file_prefix(kind)}*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    @staticmethod
    def _prune(kind):
        keep = _KEEP_BY_KIND.get(kind)

        if keep is None:
            return

        for old_path in BackupService._list_by_kind(kind)[keep:]:
            try:
                old_path.unlink()
            except OSError:
                logger.warning(
                    "Eski zaxirani o'chirib bo'lmadi: %s", old_path
                )

    @staticmethod
    def _mirror(backup_path):
        """Zaxirani qo'shimcha papkaga (agar sozlangan bo'lsa) nusxalaydi.
        Xato bo'lsa — faqat logga yoziladi: asosiy ishni to'xtatmaydi."""

        try:
            # Kechiktirilgan import — sikl (settings_service -> database)
            # va testlarda keraksiz bog'liqlikdan qochish uchun.
            from app.services.settings_service import SettingsService

            mirror_dir = SettingsService.get_setting(
                MIRROR_SETTING_KEY, ""
            ).strip()

            if not mirror_dir:
                return

            target_dir = Path(mirror_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(backup_path), str(target_dir / backup_path.name))

            # Nusxa papkasi ham to'lib ketmasin: avtomatik zaxiralardan
            # faqat oxirgilarini qoldiramiz (qo'lda olinganlarga tegmaymiz).
            for kind, keep in _KEEP_BY_KIND.items():
                files = sorted(
                    target_dir.glob(f"{_file_prefix(kind)}*.db"),
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                )

                for old_path in files[keep:]:
                    old_path.unlink(missing_ok=True)

        except Exception:
            logger.exception("Zaxirani qo'shimcha papkaga nusxalab bo'lmadi")

    @staticmethod
    def read_schema_version(db_path):
        connection = sqlite3.connect(str(db_path))

        try:
            return connection.execute("PRAGMA user_version").fetchone()[0]
        finally:
            connection.close()

    @staticmethod
    def restore_backup(backup_path):
        """Tanlangan zaxiradan bazani tiklaydi.

        Tiklashdan oldin joriy baza ham avtomatik zaxiralanadi —
        noto'g'ri fayl tanlansa ham, oldingi holatga qaytish imkoni
        qoladi. engine.dispose() Windows'da fayl almashtirish uchun
        shart: ochiq ulanishlar bo'lsa, fayl "band" xatosi chiqadi.
        """

        backup_path = Path(backup_path)

        if not backup_path.exists():
            raise ValueError("Tanlangan zaxira fayli topilmadi.")

        # Yangiroq dastur yaratgan zaxirani eski dastur tiklasa, baza
        # tuzilmasi mos kelmay qoladi — bunga yo'l qo'ymaymiz.
        if BackupService.read_schema_version(backup_path) > SCHEMA_VERSION:
            raise ValueError(
                "Bu zaxira dasturning yangiroq versiyasida yaratilgan. "
                "Avval dasturni yangilang."
            )

        if _DB_PATH.exists():
            BackupService.create_backup()

        engine.dispose()

        shutil.copy2(str(backup_path), str(_DB_PATH))
