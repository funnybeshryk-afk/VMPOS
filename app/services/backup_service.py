import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app.database.database import DATABASE_PATH, engine
from app.utils.paths import get_app_base_dir

# DATABASE_PATH bilan bitta manba — yo'l shu yerda qayta yozilmaydi,
# aks holda ikkalasi kelajakda bir-biridan ajralib qolishi mumkin.
_DB_PATH = DATABASE_PATH
# get_app_base_dir() orqali — .exe rejimida CWD emas, doim EXE
# joylashgan papkaga nisbatan (database.py'dagi kabi sabab bilan).
_BACKUP_DIR = get_app_base_dir() / "backups"


class BackupService:

    @staticmethod
    def create_backup():
        """Joriy bazadan xavfsiz nusxa — sqlite3'ning backup API'si
        orqali (oddiy fayl nusxalash emas).

        Dastur ochiq turgan paytda ham (masalan boshqa joyda
        tranzaksiya ketayotgan bo'lsa ham) izchil, buzilmagan nusxa
        kafolatlanadi — bu SQLite'ni "jonli" zaxiralashning rasmiy
        tavsiya etilgan usuli.
        """

        if not _DB_PATH.exists():
            raise ValueError("Baza fayli topilmadi.")

        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Mikrosekund aniqligi — soniya aniqligi restore_backup()
        # ichidagi avtomatik xavfsizlik nusxasi kabi tez ketma-ket
        # chaqiruvlarda to'qnashib, oldingi zaxirani jimgina ustidan
        # yozib yuborishi mumkin edi. Shu bilan birga, nomi band
        # bo'lib qolgan taqdirda ham hech qachon mavjud faylni
        # bosib o'tirmaydi — o'rniga keyingi bo'sh nomga yoziladi.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = _BACKUP_DIR / f"vmpos_{timestamp}.db"

        suffix = 1
        while backup_path.exists():
            backup_path = (
                _BACKUP_DIR / f"vmpos_{timestamp}_{suffix}.db"
            )
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

        return backup_path

    @staticmethod
    def get_backups():
        """Mavjud zaxira fayllari, eng yangisi birinchi."""

        if not _BACKUP_DIR.exists():
            return []

        return sorted(
            _BACKUP_DIR.glob("vmpos_*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

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

        if _DB_PATH.exists():
            BackupService.create_backup()

        engine.dispose()

        shutil.copy2(str(backup_path), str(_DB_PATH))
