import pytest
from PySide6.QtWidgets import QMessageBox

from app.database.migrations import prepare_database
from app.services.product_service import ProductService
from app.widgets.product_list_model import CartQtyRole


def make_product(name, price=1000, qty=10, unit="dona", tiers=None):
    return ProductService.create_product({
        "barcode": "", "name": name, "category": "X", "buy_price": 1,
        "sell_price": price, "unit": unit, "quantity": qty, "min_quantity": 1,
        "description": "", "price_tiers": tiers or [],
    })


@pytest.fixture
def page(qapp, monkeypatch):
    prepare_database()
    products = {
        "non": make_product("Non", 4000, qty=5),
        "sut": make_product("Sut", 10000, qty=50,
                            tiers=[{"min_quantity": 10, "price": 9000}]),
        "guruch": make_product("Guruch", 21000, qty=20, unit="kg"),
    }
    from app.ui.sale_page import SalePage

    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *a, **k: warnings.append(a[2] if len(a) > 2 else "")
    )
    monkeypatch.setattr("app.ui.sale_page.play_add_sound", lambda: None)
    monkeypatch.setattr("app.ui.sale_page.play_error_sound", lambda: None)

    sale_page = SalePage()
    sale_page.show()
    sale_page._warnings = warnings
    sale_page._products = products
    yield sale_page
    sale_page.close()


def ids(page):
    return {name: product.id for name, product in page._products.items()}


def test_empty_cart_shows_placeholder_and_zero_total(page):
    assert page.cart_stack.currentWidget() is page.cart_empty_state
    assert page.cart_count_label.text() == "0"
    assert "0" in page.total_label.text()


def test_plus_minus_and_remove_at_zero(page):
    non = ids(page)["non"]
    page.add_to_cart(non, 1)
    page.change_quantity(non, +1)
    assert page.cart[non]["quantity"] == 2
    assert page.cart_stack.currentWidget() is page.cart_list

    page.change_quantity(non, -1)
    assert page.cart[non]["quantity"] == 1

    page.change_quantity(non, -1)  # 0 -> qator o'chadi
    assert non not in page.cart
    assert page.cart_stack.currentWidget() is page.cart_empty_state


def test_cannot_exceed_stock_via_plus(page):
    non = ids(page)["non"]  # qoldiq 5
    page.add_to_cart(non, 5)

    page.change_quantity(non, +1)

    assert page.cart[non]["quantity"] == 5
    assert page._warnings, "qoldiq haqida ogohlantirish chiqishi kerak"


def test_wholesale_price_applies_and_reverts_with_quantity(page):
    sut = ids(page)["sut"]
    page.add_to_cart(sut, 9)
    assert page.cart[sut]["unit_price"] == 10000
    assert page.cart[sut]["is_wholesale"] is False

    page.change_quantity(sut, +1)  # 10 ta -> optom
    assert page.cart[sut]["unit_price"] == 9000
    assert page.cart[sut]["is_wholesale"] is True

    page.change_quantity(sut, -1)  # 9 ta -> yana oddiy narx
    assert page.cart[sut]["unit_price"] == 10000
    assert page.cart[sut]["is_wholesale"] is False


def test_total_and_count_follow_cart(page):
    i = ids(page)
    page.add_to_cart(i["non"], 2)   # 8 000
    page.add_to_cart(i["sut"], 1)   # 10 000

    assert page.calculate_cart_total() == 18000
    assert "18 000" in page.total_label.text()
    assert page.cart_count_label.text() == "2"


def test_catalog_cards_get_cart_quantities(page):
    non = ids(page)["non"]
    page.add_to_cart(non, 3)

    model = page.product_grid.model()
    quantities = {
        model.index(row).data(CartQtyRole) for row in range(model.rowCount())
    }
    assert 3 in quantities

    page.clear_cart()
    quantities = {
        model.index(row).data(CartQtyRole) for row in range(model.rowCount())
    }
    assert quantities == {0}


def test_weight_product_has_no_plus_minus_and_edit_updates_total(page, monkeypatch):
    guruch = ids(page)["guruch"]
    page.add_to_cart(guruch, 2)

    row = page.cart_list._rows[guruch]
    names = {b.objectName() for b in row.findChildren(type(row.quantity_button))}
    assert "qtyMinus" not in names and "qtyPlus" not in names

    class FakeDialog:
        def __init__(self, *a, **k): pass
        def exec(self): return True
        def get_quantity(self): return 2.5

    monkeypatch.setattr("app.ui.sale_page.QuantityEditDialog", FakeDialog)
    page.edit_quantity(guruch)

    assert page.cart[guruch]["quantity"] == 2.5
    assert page.calculate_cart_total() == pytest.approx(52500)


def test_delete_key_path_removes_selected_row_only(page):
    i = ids(page)
    page.add_to_cart(i["non"], 1)
    page.add_to_cart(i["sut"], 1)

    page.cart_list.select(i["non"])
    page.remove_selected_item()

    assert i["non"] not in page.cart
    assert i["sut"] in page.cart


def test_remove_without_selection_is_noop(page):
    non = ids(page)["non"]
    page.add_to_cart(non, 1)

    page.remove_selected_item()

    assert non in page.cart


def test_selection_survives_rebuild_and_clears_when_item_removed(page):
    i = ids(page)
    page.add_to_cart(i["non"], 1)
    page.cart_list.select(i["non"])

    page.change_quantity(i["non"], +1)  # qator qayta quriladi
    assert page.cart_list.selected_product_id() == i["non"]

    page.change_quantity(i["non"], -2)  # qator o'chadi
    assert page.cart_list.selected_product_id() is None


def test_rail_menu_accepts_old_and_new_entry_shapes(qapp):
    from app.widgets.sidebar_menu import SidebarMenu

    menu = SidebarMenu()
    picked = []
    menu.itemSelected.connect(picked.append)
    menu.set_groups([
        ("A", [("sale", "Sotuv", "shopping-cart")]),
        ("B", [("settings", "Sozlama", "settings", "Sozlamalar")]),
        ("C", []),
    ])

    assert menu.has_key("sale") and menu.has_key("settings")
    menu.select("settings")
    assert picked == ["settings"]
    assert menu._buttons_by_key["settings"].toolTip() == "Sozlamalar"
    assert menu._buttons_by_key["sale"].toolTip() == "Sotuv"


# ---------- haqiqiy savdo: yangi sensorli dialoglar orqali oxirigacha ----------

@pytest.fixture
def selling_page(page, monkeypatch):
    from app.services.shift_service import ShiftService

    ShiftService.open_shift("Kassir", 0)
    page.refresh_shift_panel()
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr("app.ui.sale_page.play_payment_sound", lambda: None)
    return page


def stock_of(product_id):
    return ProductService.get_product(product_id).quantity


def test_cash_sale_with_note_chip_records_change_and_stock(selling_page, monkeypatch):
    from app.services.sale_service import SaleService
    from app.ui.payment_dialog import PaymentDialog

    non = ids(selling_page)["non"]            # 4 000, qoldiq 5
    selling_page.add_to_cart(non, 2)          # jami 8 000

    def fake_exec(self):
        self._add_note(20000)                 # mijoz 20 000 berdi
        return self.ok_button.isEnabled()

    monkeypatch.setattr(PaymentDialog, "exec", fake_exec)

    selling_page.complete_sale("cash")

    sale = SaleService.get_all_sales()[0]
    assert sale.total_amount == 8000
    assert sale.paid_amount == 20000
    assert sale.change_amount == 12000
    assert stock_of(non) == 3
    assert selling_page.cart == {}


def test_cash_sale_is_not_recorded_when_underpaid(selling_page, monkeypatch):
    from app.services.sale_service import SaleService
    from app.ui.payment_dialog import PaymentDialog

    non = ids(selling_page)["non"]
    selling_page.add_to_cart(non, 2)

    def fake_exec(self):
        self._edit("clear")
        self._edit("digit", "5")              # 5 so'm — yetmaydi
        return self.ok_button.isEnabled()     # tugma o'chiq -> False

    monkeypatch.setattr(PaymentDialog, "exec", fake_exec)

    selling_page.complete_sale("cash")

    assert SaleService.get_all_sales() == []
    assert stock_of(non) == 5
    assert non in selling_page.cart


def test_mixed_sale_goes_through_touch_dialog(selling_page, monkeypatch):
    from app.services.sale_service import SaleService
    from app.ui.mixed_payment_dialog import MixedPaymentDialog

    sut = ids(selling_page)["sut"]
    selling_page.add_to_cart(sut, 1)          # 10 000

    def fake_exec(self):
        self._split(0.5)                      # 5 000 naqd + 5 000 karta
        return self.ok_button.isEnabled()

    monkeypatch.setattr(MixedPaymentDialog, "exec", fake_exec)

    selling_page.complete_sale("mixed")

    sale = SaleService.get_all_sales()[0]
    assert (sale.cash_amount, sale.card_amount) == (5000, 5000)
    assert stock_of(sut) == 49
