import os
import sqlite3
import time

import pytest

from app.database import migrations
from app.database.database import DATABASE_PATH, engine
from app.database.migrations import DatabaseTooNewError, prepare_database
from app.services.backup_service import (
    AUTO_BACKUP_INTERVAL_HOURS,
    KIND_AUTO,
    KIND_PREMIGRATE,
    BackupService,
)
from app.version import SCHEMA_VERSION


def user_version():
    connection = sqlite3.connect(str(DATABASE_PATH))
    try:
        return connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()


def columns(table):
    connection = sqlite3.connect(str(DATABASE_PATH))
    try:
        return {r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
    finally:
        connection.close()


def kinds(kind):
    return BackupService._list_by_kind(kind)


def make_old_database():
    """Eski dastur yaratgan baza: sxema versiyasi yo'q (0) va sales
    jadvalida yangi ustun (card_amount) hali yo'q."""

    prepare_database()
    engine.dispose()
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.execute("ALTER TABLE sales DROP COLUMN card_amount")
    connection.execute("PRAGMA user_version = 0")
    connection.commit()
    connection.close()
    for path in BackupService.get_backups():
        path.unlink()


def test_fresh_database_gets_schema_and_version_without_backup():
    prepare_database()

    assert user_version() == SCHEMA_VERSION
    assert "card_amount" in columns("sales")
    assert BackupService.get_backups() == []


def test_old_database_is_backed_up_then_migrated():
    make_old_database()
    assert "card_amount" not in columns("sales")

    prepare_database()

    assert "card_amount" in columns("sales")
    assert user_version() == SCHEMA_VERSION
    backups = kinds(KIND_PREMIGRATE)
    assert len(backups) == 1
    # zaxira migratsiyadan OLDINGI holatda (ustun hali yo'q)
    connection = sqlite3.connect(str(backups[0]))
    cols = {r[1] for r in connection.execute("PRAGMA table_info(sales)")}
    connection.close()
    assert "card_amount" not in cols


def test_up_to_date_database_makes_no_premigrate_backup():
    prepare_database()
    prepare_database()

    assert kinds(KIND_PREMIGRATE) == []


def test_database_newer_than_app_is_refused_and_untouched():
    prepare_database()
    engine.dispose()
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    connection.commit()
    connection.close()
    before = DATABASE_PATH.read_bytes()

    with pytest.raises(DatabaseTooNewError):
        prepare_database()

    engine.dispose()
    assert DATABASE_PATH.read_bytes() == before
    assert BackupService.get_backups() == []


def test_failed_migration_rolls_database_back(monkeypatch):
    make_old_database()
    original = migrations.apply_migrations

    def broken():
        original()  # ustunni qo'shadi...
        raise RuntimeError("yarim yo'lda yiqildi")  # ...va yiqiladi

    monkeypatch.setattr(migrations, "apply_migrations", broken)

    with pytest.raises(RuntimeError):
        prepare_database()

    engine.dispose()
    # baza migratsiyadan oldingi holatda, versiya 0 qolgan
    assert "card_amount" not in columns("sales")
    assert user_version() == 0


def test_auto_backup_runs_once_per_interval_and_prunes():
    prepare_database()

    first = BackupService.create_auto_backup_if_due()
    assert first is not None
    assert BackupService.create_auto_backup_if_due() is None  # hali erta

    # eski qilib ko'rsatamiz -> yangisi olinadi
    old = time.time() - (AUTO_BACKUP_INTERVAL_HOURS + 1) * 3600
    os.utime(first, (old, old))
    assert BackupService.create_auto_backup_if_due() is not None

    # 35 ta nusxa yaratsak ham 30 tadan ko'p qolmaydi
    for _ in range(35):
        BackupService.create_backup(KIND_AUTO)
    assert len(kinds(KIND_AUTO)) == 30


def test_manual_backups_are_never_pruned():
    prepare_database()

    for _ in range(3):
        BackupService.create_backup()
    for _ in range(35):
        BackupService.create_backup(KIND_AUTO)

    manual = [
        p for p in BackupService.get_backups()
        if not p.name.startswith(("vmpos_auto_", "vmpos_premigrate_"))
    ]
    assert len(manual) == 3


def test_auto_backup_is_mirrored_when_configured(tmp_path):
    from app.services.settings_service import SettingsService

    prepare_database()
    mirror = tmp_path / "cloud"
    SettingsService.save_setting("backup_mirror_dir", str(mirror))

    created = BackupService.create_backup(KIND_AUTO)

    assert (mirror / created.name).is_file()


def test_mirror_failure_does_not_break_backup(tmp_path):
    from app.services.settings_service import SettingsService

    prepare_database()
    blocker = tmp_path / "file_not_dir"
    blocker.write_text("x")
    SettingsService.save_setting("backup_mirror_dir", str(blocker / "sub"))

    created = BackupService.create_backup(KIND_AUTO)

    assert created.is_file()


def test_restore_refuses_backup_from_newer_schema(tmp_path):
    prepare_database()
    future = tmp_path / "vmpos_future.db"
    connection = sqlite3.connect(str(future))
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    connection.commit()
    connection.close()

    with pytest.raises(ValueError):
        BackupService.restore_backup(future)
