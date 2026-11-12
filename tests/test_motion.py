import time

import pytest
from PySide6.QtCore import QElapsedTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from app.utils import motion
from app.widgets.animated_number import AnimatedNumber
from app.widgets.cart_list import _ROW_HEIGHT, CartList
from app.widgets.product_list_model import FlashRole, ProductListModel


@pytest.fixture
def animations_on():
    motion.set_enabled(True)
    yield
    motion.set_enabled(False)


def wait_until(predicate, timeout_ms=1500):
    timer = QElapsedTimer()
    timer.start()

    while not predicate():
        if timer.elapsed() > timeout_ms:
            raise AssertionError("animatsiya vaqtida tugamadi")
        QTest.qWait(5)

    return timer.elapsed()


# ---------------- jami summa "docrutka" ----------------

def make_counter(qapp):
    label = QLabel()
    counter = AnimatedNumber(label, lambda v: f"{v:.2f}")
    label.show()

    return label, counter


def test_total_counts_up_in_time_and_ends_exact(qapp, animations_on):
    label, counter = make_counter(qapp)

    counter.set_value(1000.5)
    elapsed = wait_until(lambda: not counter.is_running())

    assert label.text() == "1000.50"            # tiyinlar yo'qolmaydi
    assert 150 <= elapsed <= 450                # ~220 ms, uzoq emas
    assert motion.DURATION_TOTAL_MS <= 260


def test_total_passes_through_intermediate_values(qapp, animations_on):
    label, counter = make_counter(qapp)
    seen = set()

    counter.set_value(100000)
    wait_until(lambda: (seen.add(counter.current()) or not counter.is_running()))

    assert any(0 < v < 100000 for v in seen)    # oraliq kadrlar bor edi
    assert counter.current() == 100000


def test_total_interrupted_continues_from_current_without_jump(qapp, animations_on):
    label, counter = make_counter(qapp)

    counter.set_value(100000)
    QTest.qWait(80)
    middle = counter.current()
    assert 0 < middle < 100000

    counter.set_value(50000)                     # yangi qiymat o'rtada
    assert counter.current() == pytest.approx(middle, abs=1)  # sakramadi
    wait_until(lambda: not counter.is_running())
    assert label.text() == "50000.00"


def test_total_is_instant_when_animations_disabled(qapp):
    label, counter = make_counter(qapp)

    counter.set_value(1234)

    assert label.text() == "1234.00" and not counter.is_running()


# ---------------- kartochka "vspishka" ----------------

def test_flash_decays_to_zero_within_duration(monkeypatch, animations_on):
    class P:
        id = 7

    model = ProductListModel()
    model.set_products([P()])
    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])

    model.flash(7)
    assert model.index(0).data(FlashRole) == pytest.approx(1.0)
    assert model.has_active_flash()

    now[0] += motion.DURATION_FLASH_MS / 1000 / 2
    mid = model.index(0).data(FlashRole)
    assert 0 < mid < 1

    now[0] += motion.DURATION_FLASH_MS / 1000        # muddat o'tdi
    assert model.index(0).data(FlashRole) == 0.0
    assert not model.has_active_flash()


def test_flash_does_nothing_when_disabled(qapp):
    class P:
        id = 1

    model = ProductListModel()
    model.set_products([P()])
    model.flash(1)

    assert model.index(0).data(FlashRole) == 0.0 and not model.has_active_flash()


# ---------------- korzina qatori ----------------

def item(name, qty=1, price=1000):
    class Product:
        pass

    product = Product()
    product.name = name
    product.unit = "dona"

    return {"product": product, "quantity": qty, "unit_price": price, "is_wholesale": False}


def test_new_row_grows_and_fades_in_existing_rows_do_not(qapp, animations_on):
    cart = CartList()
    cart.resize(400, 400)
    cart.show()

    cart.set_items({1: item("Non")})
    first_row = cart._rows[1]
    assert first_row.maximumHeight() == 0        # yangi qator 0 dan o'sadi
    wait_until(lambda: cart._rows[1].maximumHeight() == _ROW_HEIGHT)
    assert cart._rows[1].graphicsEffect() is None  # effekt olib tashlandi

    cart.set_items({1: item("Non"), 2: item("Sut")})
    assert cart._rows[1].maximumHeight() == _ROW_HEIGHT   # eskisi sakramaydi
    assert cart._rows[2].maximumHeight() == 0
    assert cart._rows[2].graphicsEffect() is not None
    wait_until(lambda: cart._rows[2].maximumHeight() == _ROW_HEIGHT)
    assert cart._rows[2].minimumHeight() == _ROW_HEIGHT == cart._rows[2].height()


def test_changed_quantity_flashes_row_then_settles(qapp, animations_on):
    cart = CartList()
    cart.resize(400, 400)
    cart.show()
    cart.set_items({1: item("Non", qty=1)})
    wait_until(lambda: cart._rows[1].maximumHeight() == _ROW_HEIGHT)

    cart.set_items({1: item("Non", qty=2)})
    row = cart._rows[1]
    QTest.qWait(40)
    assert row._flash > 0                         # yonyapti

    wait_until(lambda: row._flash == 0.0)         # va o'chadi


def test_rows_are_instant_when_animations_disabled(qapp):
    cart = CartList()
    cart.resize(400, 400)
    cart.show()

    cart.set_items({1: item("Non"), 2: item("Sut")})

    assert all(r.maximumHeight() == _ROW_HEIGHT for r in cart._rows.values())
    assert all(r.graphicsEffect() is None for r in cart._rows.values())


# ---------------- sozlama ----------------

def test_setting_round_trip_and_env_override(qapp, monkeypatch):
    from app.database.migrations import prepare_database

    prepare_database()

    motion.save_enabled(False)
    motion.set_enabled(True)                      # xotirada boshqacha
    motion.load_from_settings()
    assert motion.is_enabled() is False           # bazadan o'qildi

    motion.save_enabled(True)
    motion.set_enabled(False)
    motion.load_from_settings()
    assert motion.is_enabled() is True

    monkeypatch.setenv("VMPOS_NO_ANIM", "1")      # majburiy o'chirish
    motion.load_from_settings()
    assert motion.is_enabled() is False


def test_durations_stay_short():
    assert max(
        motion.DURATION_TOTAL_MS, motion.DURATION_ROW_MS, motion.DURATION_FLASH_MS
    ) <= 260
