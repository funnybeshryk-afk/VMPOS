import logging

from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.database import DATABASE_PATH, engine
from app.version import SCHEMA_VERSION

logger = logging.getLogger(__name__)

class DatabaseTooNewError(RuntimeError):
    """Baza dasturdan yangiroq versiyada — eski dastur uni ochmaydi."""

    def __init__(self, db_version, app_version):
        super().__init__(
            f"Baza sxemasi v{db_version}, dastur esa faqat "
            f"v{app_version} gacha biladi."
        )
        self.db_version = db_version
        self.app_version = app_version


def _register_models():
    """Barcha modellar import qilinishi shart — Base.metadata.create_all()
    ularni faqat shunda biladi. Importlar ATAYLAB statik (importlib
    emas): PyInstaller satr bilan berilgan importlarni ko'rmaydi va
    .exe'ga modelni qo'shmay qoldirardi. Yangi model qo'shsangiz — shu
    yerga ham qo'shing."""

    import app.models.app_setting  # noqa: F401
    import app.models.customer  # noqa: F401
    import app.models.debt_payment  # noqa: F401
    import app.models.price_tier  # noqa: F401
    import app.models.product  # noqa: F401
    import app.models.refund  # noqa: F401
    import app.models.sale  # noqa: F401
    import app.models.shift  # noqa: F401
    import app.models.stock_receipt  # noqa: F401
    import app.models.supplier  # noqa: F401
    import app.models.user  # noqa: F401


def _read_schema_version():
    with engine.connect() as connection:
        return connection.exec_driver_sql("PRAGMA user_version").scalar()


def _write_schema_version(version):
    # PRAGMA parametr qabul qilmaydi; version — bizning o'zimizning int.
    with engine.begin() as connection:
        connection.exec_driver_sql(f"PRAGMA user_version = {int(version)}")


def prepare_database():
    """Dastur ochilganda bazani xavfsiz tayyorlaydi:

    1. Baza dasturdan yangiroq bo'lsa — DatabaseTooNewError (hech narsaga
       tegmaydi).
    2. Mavjud baza eski sxemada bo'lsa — migratsiyadan OLDIN avtomatik
       zaxira oladi.
    3. Jadvallarni yaratadi, ustunlarni qo'shadi (apply_migrations).
    4. Migratsiya yarim yo'lda yiqilsa — bazani zaxiradan avtomatik
       tiklaydi va xatoni yuqoriga uzatadi (yarim-migratsiyalangan baza
       qolmaydi).
    5. Sxema versiyasini belgilaydi.

    Yangi (bo'sh) baza uchun zaxira olinmaydi — saqlanadigan narsa yo'q.
    """

    # Kechiktirilgan import — backup_service ham shu paketga bog'liq.
    from app.services.backup_service import BackupService, KIND_PREMIGRATE

    _register_models()

    existed = (
        DATABASE_PATH.exists() and DATABASE_PATH.stat().st_size > 0
    )
    backup_path = None

    if existed:
        db_version = _read_schema_version()

        if db_version > SCHEMA_VERSION:
            raise DatabaseTooNewError(db_version, SCHEMA_VERSION)

        if db_version < SCHEMA_VERSION:
            backup_path = BackupService.create_backup(KIND_PREMIGRATE)
            logger.info(
                "Migratsiyadan oldingi zaxira: %s (baza v%s -> v%s)",
                backup_path,
                db_version,
                SCHEMA_VERSION,
            )

    try:
        Base.metadata.create_all(bind=engine)
        apply_migrations()
        _write_schema_version(SCHEMA_VERSION)
    except Exception:
        logger.exception("Migratsiya yiqildi")

        if backup_path is not None:
            try:
                BackupService.restore_backup(backup_path)
                logger.warning(
                    "Baza migratsiyadan oldingi holatga qaytarildi: %s",
                    backup_path,
                )
            except Exception:
                logger.exception(
                    "Bazani zaxiradan tiklab bo'lmadi: %s", backup_path
                )

        raise


def apply_migrations():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    migrations = {
        "sales": {
            "payment_method": (
                "VARCHAR(20) NOT NULL DEFAULT 'cash'"
            ),
            "paid_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "change_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "status": (
                "VARCHAR(20) NOT NULL DEFAULT 'completed'"
            ),
            "cash_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "card_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "vat_total": "FLOAT NOT NULL DEFAULT 0",
            "fiscal_status": "VARCHAR(20) NOT NULL DEFAULT 'none'",
            "fiscal_receipt_id": "VARCHAR(64)",
            "fiscal_sign": "VARCHAR(255)",
            "fiscal_qr_url": "VARCHAR(512)",
            "fiscal_at": "DATETIME",
            "fiscal_error": "TEXT",
            "fiscal_attempts": "INTEGER NOT NULL DEFAULT 0",
        },
        "stock_receipts": {
            "supplier_id": "INTEGER",
            "supplier_name": "VARCHAR(255)",
        },
        "customers": {
            "debt_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "debt_date": "DATE",
        },
        "shifts": {
            "cashier_user_id": "INTEGER",
        },
        "products": {
            "image_path": "VARCHAR(255)",
            "ikpu_code": "VARCHAR(20)",
            "package_code": "VARCHAR(20)",
            "vat_rate": "FLOAT",
        },
        "debt_payments": {
            "type": "VARCHAR(20) NOT NULL DEFAULT 'payment'",
            "cashier_name": "VARCHAR(255)",
            "cashier_user_id": "INTEGER",
            "sale_id": "INTEGER",
            "shift_id": "INTEGER",
        },
        "sale_items": {
            "returned_quantity": "FLOAT NOT NULL DEFAULT 0",
            "ikpu_code": "VARCHAR(20)",
            "package_code": "VARCHAR(20)",
            "vat_rate": "FLOAT NOT NULL DEFAULT 0",
            "vat_amount": "FLOAT NOT NULL DEFAULT 0",
        },
        "refunds": {
            "vat_total": "FLOAT NOT NULL DEFAULT 0",
            "fiscal_status": "VARCHAR(20) NOT NULL DEFAULT 'none'",
            "fiscal_receipt_id": "VARCHAR(64)",
            "fiscal_sign": "VARCHAR(255)",
            "fiscal_qr_url": "VARCHAR(512)",
            "fiscal_at": "DATETIME",
            "fiscal_error": "TEXT",
            "fiscal_attempts": "INTEGER NOT NULL DEFAULT 0",
        },
        "refund_items": {
            "vat_amount": "FLOAT NOT NULL DEFAULT 0",
        },
    }

    with engine.begin() as connection:
        for table_name, new_columns in migrations.items():
            if table_name not in table_names:
                continue

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            newly_added_columns = set()

            for column_name, column_definition in new_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} "
                            f"{column_definition}"
                        )
                    )
                    newly_added_columns.add(column_name)

            # cash_amount/card_amount birinchi marta qo'shilganda eski
            # savdolarda ikkalasi ham 0 bo'lib qoladi — hisobotlarda
            # eski kunlar naqd/karta jamidan yo'qolib qoladi. Eski
            # yozuvlarni payment_method asosida qayta tiklaymiz: bu
            # ustunlar paydo bo'lishidan oldin "mixed" umuman
            # saqlanmagan (eski xato tufayli har doim "cash" yoki
            # "card" bo'lib yozilgan), shuning uchun bu tiklash aniq.
            if (
                table_name == "sales"
                and "cash_amount" in newly_added_columns
            ):
                connection.execute(
                    text(
                        "UPDATE sales SET "
                        "cash_amount = CASE "
                        "WHEN payment_method = 'card' THEN 0 "
                        "ELSE total_amount END, "
                        "card_amount = CASE "
                        "WHEN payment_method = 'card' THEN total_amount "
                        "ELSE 0 END"
                    )
                )
