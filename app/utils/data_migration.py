"""Eski joylashuvdan (exe yonidagi papka) yangi ma'lumotlar papkasiga
BIR MARTALIK ko'chirish.

Eski versiyalarda baza, zaxiralar va mahsulot rasmlari .exe turgan
papkada saqlangan. Endi ular dastur papkasidan alohida turadi
(paths.get_data_dir()). Yangilanishdan keyin kassir hech narsani
sezmasligi kerak: birinchi ishga tushishda ma'lumotlar o'zi ko'chadi.

Ko'chirish NUSXALASH orqali bajariladi — eski fayllar o'chirilmaydi
(xato bo'lsa, qaytish yo'li qoladi). Baza SQLite backup API orqali
ko'chiriladi, shuning uchun izchil nusxa kafolatlanadi.
"""

import logging
import shutil
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_NAME = "vmpos.db"
_NOTE_NAME = "VMPOS_KOCHIRILGAN.txt"
_IMAGES_REL = Path("assets") / "products"


def _copy_database(source_db, target_db):
    source = sqlite3.connect(str(source_db))

    try:
        destination = sqlite3.connect(str(target_db))

        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()


def _copy_tree(source_dir, target_dir):
    if not source_dir.is_dir():
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0

    for item in source_dir.iterdir():
        if not item.is_file():
            continue

        destination = target_dir / item.name

        if not destination.exists():
            shutil.copy2(str(item), str(destination))
            copied += 1

    return copied


def _make_image_paths_relative(db_path, images_dir):
    """products.image_path avval MUTLAQ yo'l bo'lib saqlangan (eski exe
    papkasiga ishora qiladi). Yangi papkada fayl bor bo'lsa — nisbiy
    ko'rinishga o'tkazamiz."""

    connection = sqlite3.connect(str(db_path))

    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if "products" not in tables:
            return 0

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(products)")
        }

        if "image_path" not in columns:
            return 0

        rows = connection.execute(
            "SELECT id, image_path FROM products "
            "WHERE image_path IS NOT NULL AND image_path != ''"
        ).fetchall()

        updated = 0

        for product_id, image_path in rows:
            # Windows ("C:\...\x.png") va POSIX yo'llarini ham to'g'ri
            # kesish uchun ikkala ajratgich bo'yicha bo'lamiz.
            file_name = image_path.replace("\\", "/").rsplit("/", 1)[-1]

            if not (images_dir / file_name).is_file():
                continue

            new_value = (_IMAGES_REL / file_name).as_posix()

            if new_value != image_path:
                connection.execute(
                    "UPDATE products SET image_path = ? WHERE id = ?",
                    (new_value, product_id),
                )
                updated += 1

        connection.commit()

        return updated

    finally:
        connection.close()


def migrate_legacy_data(legacy_dir, data_dir):
    """legacy_dir (eski, exe yonidagi papka) -> data_dir (yangi).

    Faqat yangi papkada baza YO'Q va eski papkada BOR bo'lsa ishlaydi;
    qayta chaqirilsa hech narsa qilmaydi. Qaytaradi: ko'chirildimi (bool).
    """

    legacy_dir = Path(legacy_dir)
    data_dir = Path(data_dir)

    if legacy_dir.resolve() == data_dir.resolve():
        return False

    legacy_db = legacy_dir / _DB_NAME
    target_db = data_dir / _DB_NAME

    if target_db.exists() or not legacy_db.is_file():
        return False

    data_dir.mkdir(parents=True, exist_ok=True)

    # Avval vaqtinchalik nomga yozamiz, oxirida almashtiramiz: ko'chirish
    # yarim yo'lda uzilsa, vmpos.db "yarim-tayyor" bo'lib qolmaydi va
    # keyingi ishga tushishda urinish qaytadan boshlanadi.
    temp_db = data_dir / (_DB_NAME + ".kochirilmoqda")
    temp_db.unlink(missing_ok=True)

    _copy_database(legacy_db, temp_db)

    images_copied = _copy_tree(
        legacy_dir / _IMAGES_REL, data_dir / _IMAGES_REL
    )
    backups_copied = _copy_tree(
        legacy_dir / "backups", data_dir / "backups"
    )
    paths_fixed = _make_image_paths_relative(
        temp_db, data_dir / _IMAGES_REL
    )

    temp_db.replace(target_db)

    logger.info(
        "Eski ma'lumotlar ko'chirildi: %s -> %s "
        "(rasm: %s, zaxira: %s, rasm yo'li tuzatildi: %s)",
        legacy_dir,
        data_dir,
        images_copied,
        backups_copied,
        paths_fixed,
    )

    # Eski papkada qolgan baza "qaysi biri haqiqiy?" degan chalkashlik
    # tug'dirmasligi uchun izoh qoldiramiz (yozib bo'lmasa — muhim emas).
    try:
        (legacy_dir / _NOTE_NAME).write_text(
            "Bu papkadagi baza yangi joyga ko'chirilgan.\n"
            f"Joriy ma'lumotlar: {data_dir}\n"
            "Bu yerdagi eski nusxa endi ishlatilmaydi.\n",
            encoding="utf-8",
        )
    except OSError:
        pass

    return True
