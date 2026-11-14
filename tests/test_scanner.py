import time

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox, QPushButton

from app.database.database import SessionLocal
from app.database.migrations import prepare_database
from app.models.product import Product
from app.services.product_service import ProductService

CODE_A = "4780000000011"
CODE_B = "4780000000028"


def make_product(name, barcode, category="X", unit="dona"):
    return ProductService.create_product({
        "barcode": barcode, "name": name, "category": category, "buy_price": 1,
        "sell_price": 1000, "unit": unit, "quantity": 100, "min_quantity": 5,
        "description": "", "price_tiers": [],
    })


@pytest.fixture
def page(qapp, monkeypatch):
    prepare_database()
    make_product("Non", CODE_A, "Non")
    make_product("Sut", CODE_B, "Sut mahsulotlari")
    monkeypatch.setattr("app.ui.sale_page.play_add_sound", lambda: None)
    monkeypatch.setattr("app.ui.sale_page.play_error_sound", lambda: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)

    from app.ui.sale_page import SalePage

    # Oldingi testlardan qolgan ochiq oynalar faollashuvga xalaqit bermasin.
    QApplication.closeAllWindows()
    QTest.qWait(20)

    sale_page = SalePage()
    sale_page.resize(1200, 700)
    sale_page.show()

    for _ in range(40):                       # faollashishini kutamiz (<= ~1 s)
        sale_page.activateWindow()
        QTest.qWait(25)

        if QApplication.activeWindow() is sale_page:
            break

    assert QApplication.activeWindow() is sale_page, "oyna faol bo'lmadi"
    yield sale_page
    sale_page.close()


def quantity_in_cart(page):
    return sum(item["quantity"] for item in page.cart.values())


def scan(page, code=CODE_A):
    """Haqiqiy skaner kabi: raqamlar va Enter FAQAT hozir fokusdagi vidjetga."""

    focus = QApplication.focusWidget()
    assert focus is not None, "fokus hech qaysi vidjetda emas"

    before = quantity_in_cart(page)

    for char in code:
        QTest.keyClick(QApplication.focusWidget() or focus, char)

    QTest.keyClick(QApplication.focusWidget() or focus, Qt.Key_Return)
    QTest.qWait(30)

    return quantity_in_cart(page) - before


def test_scan_works_on_fresh_page(page):
    assert scan(page) == 1


def test_scan_works_after_tapping_a_category(page):
    tiles = [b for b in page.category_bar.findChildren(QPushButton) if b.objectName() == "categoryTile"]
    QTest.mouseClick(tiles[1], Qt.LeftButton)

    assert QApplication.focusWidget() is page.search_edit
    assert scan(page) == 1


def test_scan_works_after_tapping_a_product_card(page):
    grid = page.product_grid
    rect = grid.visualRect(grid.model().index(0))
    QTest.mouseClick(grid.viewport(), Qt.LeftButton, pos=rect.center())
    page.cart.clear()
    page.update_cart_table()

    assert QApplication.focusWidget() is page.search_edit
    assert scan(page, CODE_B) == 1


def test_scan_works_after_cart_stepper_and_row_taps(page):
    page.add_to_cart(page.products[0].id, 1)
    row = next(iter(page.cart_list._rows.values()))
    plus = next(b for b in row.findChildren(QPushButton) if b.objectName() == "qtyPlus")

    QTest.mouseClick(plus, Qt.LeftButton)           # qator qayta quriladi
    QTest.mouseClick(next(iter(page.cart_list._rows.values())), Qt.LeftButton, pos=QPoint(20, 20))

    assert QApplication.focusWidget() is page.search_edit
    assert scan(page, page.products[0].barcode) == 1


def test_scan_works_after_clear_cart_button(page):
    page.add_to_cart(page.products[0].id, 1)
    QTest.mouseClick(page.new_sale_button, Qt.LeftButton)

    assert scan(page) == 1


def test_unknown_barcode_does_not_add_and_next_scan_replaces_leftover(page):
    assert scan(page, "9999999999999") == 0
    assert scan(page, CODE_A) == 1                   # qolgan matn almashtirildi


# ---------------- himoya filtri: fokus noto'g'ri joyga tushsa ----------------

def force_focus_on_button(page):
    button = QPushButton("Fokusli tugma", page)
    button.setFocusPolicy(Qt.StrongFocus)
    button.show()
    button.setFocus()
    QTest.qWait(20)
    assert QApplication.focusWidget() is button

    return button


def test_digits_are_redirected_from_any_focused_widget_to_search(page):
    force_focus_on_button(page)

    assert scan(page) == 1                            # filtr yo'naltirdi
    assert QApplication.focusWidget() is page.search_edit


def test_capture_does_not_steal_from_other_text_fields(page):
    other = QLineEdit(page)
    other.show()
    other.setFocus()
    QTest.qWait(20)

    QTest.keyClicks(other, "123")

    assert other.text() == "123" and page.search_edit.text() == ""


def test_capture_ignores_shortcuts_and_non_text_keys(page):
    button = force_focus_on_button(page)

    QTest.keyClick(button, Qt.Key_F2)                # matnsiz
    assert page._scan_capture._should_capture(
        type("E", (), {"modifiers": lambda s: Qt.ControlModifier, "text": lambda s: "5"})()
    ) is False                                       # Ctrl+5


def test_capture_is_off_while_a_modal_dialog_is_open(page, monkeypatch):
    force_focus_on_button(page)
    monkeypatch.setattr(QApplication, "activeModalWidget", staticmethod(lambda: object()))

    QTest.keyClick(QApplication.focusWidget(), "7")

    assert page.search_edit.text() == ""             # dialog ichiga aralashmadi


def test_capture_is_off_when_page_is_hidden(page):
    force_focus_on_button(page)
    page.hide()

    assert page._scan_capture._should_capture(
        type("E", (), {"modifiers": lambda s: Qt.NoModifier, "text": lambda s: "7"})()
    ) is False


# ---------------- tezlik ----------------

def bulk_products(count):
    session = SessionLocal()
    session.add_all([
        Product(
            barcode=f"59000{i:08d}", name=f"Mahsulot {i}", category=f"K{i % 9}",
            buy_price=1, sell_price=2000 + i, unit="dona", quantity=50,
            min_quantity=5, description="",
        )
        for i in range(count)
    ])
    session.commit()
    session.close()


def test_hidden_list_table_is_not_built_while_grid_is_shown(page):
    bulk_products(400)
    page.load_products()

    assert page.products_table.rowCount() == 0       # yashirin jadval qurilmaydi
    page.search_products("Mahsulot 1")
    assert page.products_table.rowCount() == 0


def test_scan_on_a_large_catalog_is_fast(page):
    bulk_products(1500)
    page.load_products()
    QTest.qWait(30)

    code = "5900000001499"
    started = time.monotonic()

    for char in code:
        QTest.keyClick(page.search_edit, char)

    QTest.keyClick(page.search_edit, Qt.Key_Return)
    elapsed = time.monotonic() - started

    assert quantity_in_cart(page) == 1
    # Avval ~0,7 s HAR BIR harfga (13 harf ~ 9 s). Katta zaxira bilan chegara.
    assert elapsed < 2.0, f"skaner juda sekin: {elapsed:.2f}s"


def test_list_view_is_built_on_demand_with_current_filter_and_works(page):
    bulk_products(30)
    page.load_products()
    page.search_products("Mahsulot 2")                # Mahsulot 2, 20..29
    expected = len(page._shown_products)

    page.set_view_mode("list")

    table = page.products_table
    assert table.rowCount() == expected and expected == 11
    assert table.item(0, 4).text() in ("Yetarli", "Kam qoldi", "Tugagan")

    page.cart.clear()
    page.on_product_double_clicked(0, 0)             # qo'sh bosish -> savatga
    assert quantity_in_cart(page) == 1
    assert table.cellWidget(0, 4) is None            # vidjetsiz (tez)
