import sqlite3

import pytest

from app.database.database import DATABASE_PATH, engine
from app.database.migrations import prepare_database
from app.services.backup_service import KIND_PREMIGRATE, BackupService
from app.services.product_service import ProductService
from app.services.refund_service import RefundService
from app.services.sale_service import SaleService
from app.services.settings_service import SettingsService
from app.utils import vat
from app.version import SCHEMA_VERSION


def make_product(name, price, qty=100, ikpu="", package="", vat_rate=None):
    return ProductService.create_product({
        "barcode": "", "name": name, "category": "X", "buy_price": 1,
        "sell_price": price, "unit": "dona", "quantity": qty,
        "min_quantity": 1, "description": "", "price_tiers": [],
        "ikpu_code": ikpu, "package_code": package, "vat_rate": vat_rate,
    })


def sell(*pairs):
    cart = {p.id: {"product": p, "quantity": q} for p, q in pairs}
    total = sum(p.sell_price * q for p, q in pairs)

    return SaleService.create_sale(cart, "cash", total)


@pytest.fixture(autouse=True)
def db(qapp):
    prepare_database()


# ---------------- QQS hisob ----------------

def test_vat_is_extracted_from_inclusive_price():
    assert vat.vat_included(112000, 12) == 12000.0
    assert vat.vat_included(112, 12) == 12.0


def test_vat_rounds_half_up_to_tiyin():
    # 100.05 * 12 / 112 = 10.7196... -> 10.72
    assert vat.vat_included(100.05, 12) == 10.72
    # aniq yarim: 0.5 * ... tekshiruv — 1.00 * 12/112 = 0.10714 -> 0.11
    assert vat.vat_included(1, 12) == 0.11


@pytest.mark.parametrize("rate", [0, None, -5])
def test_zero_or_missing_rate_gives_no_vat(rate):
    assert vat.vat_included(50000, rate) == 0.0


def test_effective_rate_distinguishes_zero_from_unset():
    assert vat.effective_vat_rate(None, 12) == 12     # bo'sh -> standart
    assert vat.effective_vat_rate(0, 12) == 0         # aniq 0 — QQSsiz
    assert vat.effective_vat_rate(15, 12) == 15


def test_validators():
    assert vat.validate_ikpu(" 1234 5678 ") == "12345678"
    assert vat.validate_ikpu("") == ""
    assert vat.validate_vat_rate("12,5") == 12.5
    assert vat.validate_vat_rate("") is None
    assert vat.validate_tin("123 456 789") == "123456789"
    for bad in ("12a", "1" * 21):
        with pytest.raises(ValueError):
            vat.validate_ikpu(bad)
    for bad in ("abc", "-1", "101"):
        with pytest.raises(ValueError):
            vat.validate_vat_rate(bad)
    with pytest.raises(ValueError):
        vat.validate_tin("12345678901234567")


# ---------------- mahsulot ----------------

def test_product_stores_and_updates_fiscal_fields():
    p = make_product("Non", 4000, ikpu="12345678901234567", package="1234", vat_rate=12)
    stored = ProductService.get_product(p.id)
    assert (stored.ikpu_code, stored.package_code, stored.vat_rate) == ("12345678901234567", "1234", 12)

    data = {
        "barcode": stored.barcode, "name": "Non", "category": "X",
        "buy_price": 1, "sell_price": 4000, "unit": "dona", "quantity": 100,
        "min_quantity": 1, "description": "", "price_tiers": [],
        "ikpu_code": "", "package_code": "", "vat_rate": None,
    }
    ProductService.update_product(p.id, data)
    cleared = ProductService.get_product(p.id)
    assert (cleared.ikpu_code, cleared.package_code, cleared.vat_rate) == (None, None, None)


def test_update_without_fiscal_keys_leaves_fiscal_values_untouched():
    p = make_product("Non", 4000, ikpu="111", vat_rate=12)
    legacy_data = {
        "barcode": ProductService.get_product(p.id).barcode, "name": "Non 2",
        "category": "X", "buy_price": 1, "sell_price": 4000, "unit": "dona",
        "quantity": 100, "min_quantity": 1, "description": "", "price_tiers": [],
    }
    ProductService.update_product(p.id, legacy_data)

    stored = ProductService.get_product(p.id)
    assert stored.name == "Non 2" and stored.ikpu_code == "111" and stored.vat_rate == 12


def test_invalid_fiscal_values_are_rejected_without_creating_product():
    for kwargs in ({"ikpu": "ab12"}, {"package": "x"}, {"vat_rate": 150}):
        with pytest.raises(ValueError):
            make_product("Bad", 1000, **kwargs)

    assert ProductService.get_fiscal_gaps()["total"] == 0


def test_fiscal_gaps_count_missing_codes():
    make_product("A", 1000, ikpu="1", package="1")
    make_product("B", 1000, ikpu="1")
    make_product("C", 1000)

    assert ProductService.get_fiscal_gaps() == {
        "total": 3, "missing_ikpu": 1, "missing_package": 2,
    }


# ---------------- sotuv: QQS "surat" ----------------

def test_sale_snapshots_vat_per_line_and_totals():
    SettingsService.save_fiscal_settings({"default_vat_rate": "12"})
    a = make_product("A", 112000, ikpu="111", package="9", vat_rate=12)
    b = make_product("B", 11200)                 # stavka yo'q -> standart 12
    c = make_product("C", 5000, vat_rate=0)      # aniq 0 — QQSsiz

    sale = sell((a, 1), (b, 3), (c, 2))
    items = {i.product_name: i for i in SaleService.get_sale_items(sale.id)}

    assert (items["A"].vat_rate, items["A"].vat_amount) == (12, 12000.0)
    assert (items["A"].ikpu_code, items["A"].package_code) == ("111", "9")
    assert (items["B"].vat_rate, items["B"].vat_amount) == (12, 3600.0)  # 33 600 ichidan
    assert (items["C"].vat_rate, items["C"].vat_amount) == (0, 0.0)
    assert SaleService.get_sale(sale.id).vat_total == 15600.0


def test_sale_snapshot_survives_later_product_changes():
    p = make_product("A", 112000, ikpu="111", vat_rate=12)
    sale = sell((p, 1))

    data = {
        "barcode": ProductService.get_product(p.id).barcode, "name": "A",
        "category": "X", "buy_price": 1, "sell_price": 112000, "unit": "dona",
        "quantity": 99, "min_quantity": 1, "description": "", "price_tiers": [],
        "ikpu_code": "999", "package_code": "", "vat_rate": 0,
    }
    ProductService.update_product(p.id, data)

    item = SaleService.get_sale_items(sale.id)[0]
    assert (item.ikpu_code, item.vat_rate, item.vat_amount) == ("111", 12, 12000.0)


def test_fiscal_status_follows_mode_setting():
    p = make_product("A", 1000)
    assert SaleService.get_sale(sell((p, 1)).id).fiscal_status == "none"

    SettingsService.save_setting("fiscal_mode", "test-provider")
    assert SaleService.get_sale(sell((p, 1)).id).fiscal_status == "pending"


# ---------------- qaytarish ----------------

def test_refund_uses_original_vat_rate_not_current():
    p = make_product("A", 112000, vat_rate=12, qty=10)
    sale = sell((p, 2))                                   # QQS 24 000
    item = SaleService.get_sale_items(sale.id)[0]

    data = {
        "barcode": ProductService.get_product(p.id).barcode, "name": "A",
        "category": "X", "buy_price": 1, "sell_price": 112000, "unit": "dona",
        "quantity": 8, "min_quantity": 1, "description": "", "price_tiers": [],
        "ikpu_code": "", "package_code": "", "vat_rate": 0,   # keyin QQSsiz qilindi
    }
    ProductService.update_product(p.id, data)

    refund = RefundService.create_refund(
        sale.id, [{"sale_item_id": item.id, "quantity": 1}]
    )

    assert refund.vat_total == 12000.0                    # 12% bo'yicha, 0% emas

    from app.database.database import SessionLocal
    from app.models.refund import RefundItem

    session = SessionLocal()
    try:
        amounts = [r.vat_amount for r in session.query(RefundItem).filter_by(refund_id=refund.id)]
    finally:
        session.close()
    assert amounts == [12000.0]


def test_refund_fiscal_status_requires_fiscalized_original():
    p = make_product("A", 1000, qty=10)
    plain = sell((p, 1))
    item = SaleService.get_sale_items(plain.id)[0]
    r1 = RefundService.create_refund(plain.id, [{"sale_item_id": item.id, "quantity": 1}])
    assert r1.fiscal_status == "none"

    SettingsService.save_setting("fiscal_mode", "test-provider")
    fiscalized = sell((p, 1))                              # pending
    item2 = SaleService.get_sale_items(fiscalized.id)[0]
    r2 = RefundService.create_refund(fiscalized.id, [{"sale_item_id": item2.id, "quantity": 1}])
    assert r2.fiscal_status == "pending"


# ---------------- sozlamalar ----------------

def test_fiscal_settings_round_trip_and_validation_is_atomic():
    SettingsService.save_fiscal_settings(
        {"store_tin": "123 456 789", "store_legal_name": " Vodiy Market MChJ ", "default_vat_rate": "12"}
    )
    s = SettingsService.get_fiscal_settings()
    assert (s["store_tin"], s["store_legal_name"], s["default_vat_rate"]) == ("123456789", "Vodiy Market MChJ", 12.0)
    assert s["fiscal_mode"] == "off"

    with pytest.raises(ValueError):
        SettingsService.save_fiscal_settings(
            {"store_tin": "999999999", "store_legal_name": "X", "default_vat_rate": "abc"}
        )
    assert SettingsService.get_fiscal_settings()["store_tin"] == "123456789"   # o'zgarmadi


# ---------------- migratsiya v1 -> v2 ----------------

NEW_COLUMNS = {
    "products": ["ikpu_code", "package_code", "vat_rate"],
    "sale_items": ["ikpu_code", "package_code", "vat_rate", "vat_amount"],
    "sales": ["vat_total", "fiscal_status", "fiscal_receipt_id", "fiscal_sign",
              "fiscal_qr_url", "fiscal_at", "fiscal_error", "fiscal_attempts"],
    "refunds": ["vat_total", "fiscal_status", "fiscal_receipt_id", "fiscal_sign",
                "fiscal_qr_url", "fiscal_at", "fiscal_error", "fiscal_attempts"],
    "refund_items": ["vat_amount"],
}


def columns(connection, table):
    return {r[1] for r in connection.execute(f"PRAGMA table_info({table})")}


def test_schema_version_is_2():
    assert SCHEMA_VERSION == 2


def test_v1_database_is_upgraded_keeping_data():
    p = make_product("Non", 4000)
    sale = sell((p, 2))
    engine.dispose()

    connection = sqlite3.connect(str(DATABASE_PATH))
    for table, cols in NEW_COLUMNS.items():
        for col in cols:
            connection.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
    connection.execute("PRAGMA user_version = 1")
    connection.commit()
    connection.close()
    for path in BackupService.get_backups():
        path.unlink()

    prepare_database()                                      # v1 -> v2

    engine.dispose()
    connection = sqlite3.connect(str(DATABASE_PATH))
    try:
        for table, cols in NEW_COLUMNS.items():
            assert set(cols) <= columns(connection, table), table
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        row = connection.execute(
            "SELECT total_amount, vat_total, fiscal_status, fiscal_attempts FROM sales WHERE id=?",
            (sale.id,),
        ).fetchone()
        assert row == (8000.0, 0.0, "none", 0)              # eski chek saqlandi
    finally:
        connection.close()

    assert len(BackupService._list_by_kind(KIND_PREMIGRATE)) == 1   # migratsiyadan oldin zaxira
