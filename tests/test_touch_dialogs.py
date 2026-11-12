from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from app.ui.customer_picker_dialog import CustomerPickerDialog
from app.ui.mixed_payment_dialog import MixedPaymentDialog
from app.ui.payment_dialog import PaymentDialog
from app.ui.quantity_edit_dialog import QuantityEditDialog
from app.ui.weight_dialog import WeightDialog


def product(unit="dona", qty=5, price=4000, name="Non"):
    return SimpleNamespace(name=name, unit=unit, quantity=qty, sell_price=price)


def press(dialog, *digits):
    for d in digits:
        dialog._edit("digit", d)


# ---------------- miqdor / og'irlik ----------------

def test_quantity_validates_range_live(qapp):
    d = QuantityEditDialog(product(qty=5), 3)
    assert d.ok_button.isEnabled() and d.get_quantity() == 3

    press(d, "9")                       # tayyor 3 almashadi -> 9 > qoldiq 5
    assert not d.ok_button.isEnabled()
    assert "Qoldiq yetarli emas" in d._hint.text()
    assert d._field.property("state") == "bad"

    d._edit("backspace")                # 0 -> eng kami 1
    assert not d.ok_button.isEnabled()

    press(d, "4")
    assert d.ok_button.isEnabled() and d.get_quantity() == 4


def test_piece_quantity_has_no_decimal_point(qapp):
    d = QuantityEditDialog(product(qty=50), 1)
    press(d, "1"); d._edit("decimal"); press(d, "5")
    assert d.get_quantity() == 15       # vergul e'tiborsiz


def test_weight_decimal_presets_and_total(qapp):
    kg = product(unit="kg", qty=20, price=21000, name="Guruch")
    d = WeightDialog(kg, price_for=lambda q: 21000)
    assert d.get_weight() == 1

    press(d, "2"); d._edit("decimal"); press(d, "5")
    assert d.get_weight() == 2.5
    assert "52 500" in d._hint.text()

    d._preset(0.5)
    assert d.get_weight() == 0.5

    press(d, "3", "0")                  # 30 kg > 20
    assert not d.ok_button.isEnabled()


def test_physical_keyboard_still_works(qapp):
    d = QuantityEditDialog(product(qty=50), 1)
    d.show()
    QTest.keyClick(d, Qt.Key_2)
    QTest.keyClick(d, Qt.Key_5)
    assert d.get_quantity() == 25
    QTest.keyClick(d, Qt.Key_Backspace)
    assert d.get_quantity() == 2


# ---------------- to'lov ----------------

def test_payment_exact_prefill_and_change(qapp):
    d = PaymentDialog(84000, None)
    assert d.ok_button.isEnabled()
    assert d.get_payment_data() == ("cash", 84000)

    press(d, "5")                        # 5 so'm — yetmaydi
    assert not d.ok_button.isEnabled()
    assert "Yetmayapti" in d._change.text()

    d._add_note(100000)                  # tayyor/yozilgan summani almashtiradi? yozilgan -> qo'shadi
    assert d.get_payment_data()[1] == 100005
    d._exact()
    d._add_note(100000)                  # tegilmagan tayyor summa ustiga — almashtiradi
    assert d.get_payment_data() == ("cash", 100000)
    assert "16 000" in d._change.text() and d.ok_button.isEnabled()


def test_payment_card_tab_disables_pad_and_pays_exact(qapp):
    d = PaymentDialog(84000, None)
    d.card_tab.setChecked(True)

    assert d.get_payment_data() == ("card", 84000)
    assert not d._pad.isEnabled()
    assert d.ok_button.isEnabled()

    d.cash_tab.setChecked(True)
    assert d._pad.isEnabled()


def test_payment_fixed_cash_has_no_tabs(qapp):
    d = PaymentDialog(1000, "cash")
    assert d.cash_tab is None and d.card_tab is None


def test_cash_payment_below_total_cannot_be_confirmed(qapp):
    d = PaymentDialog(84000, "cash")
    press(d, "8", "3", "9", "9", "9")
    assert not d.ok_button.isEnabled()
    press(d, "0")                        # 839990 ... emas, qo'shiladi
    assert d.ok_button.isEnabled()


# ---------------- aralash ----------------

def test_mixed_auto_complements_other_field(qapp):
    d = MixedPaymentDialog(84000)
    assert d.get_payment_data() == (84000, 0) and d.ok_button.isEnabled()

    d._activate("card")
    press(d, "2", "0", "0", "0", "0")
    assert d.get_payment_data() == (64000, 20000)
    assert d.ok_button.isEnabled()


def test_mixed_overpay_is_rejected(qapp):
    d = MixedPaymentDialog(84000)
    press(d, "1", "0", "0", "0", "0", "0")      # naqd 100 000 > jami
    assert d.get_payment_data() == (100000, 0)
    assert not d.ok_button.isEnabled()
    assert "Ortiqcha" in d._hint.text()


def test_mixed_split_chips(qapp):
    d = MixedPaymentDialog(84000)
    d._split(0.5)
    assert d.get_payment_data() == (42000, 42000)
    d._split(0)
    assert d.get_payment_data() == (0, 84000)


# ---------------- nasiya ----------------

def customers():
    return [
        SimpleNamespace(id=1, name="Bobur", phone="+998 93", debt_amount=185000),
        SimpleNamespace(id=2, name="Malika", phone="", debt_amount=0),
    ]


def test_debt_defaults_and_chips(qapp):
    d = CustomerPickerDialog(customers(), 84000)
    assert d.get_debt_amount() == 84000
    d._set_debt(0.5)
    assert d.get_debt_amount() == 42000
    assert d.get_selected_customer().name == "Bobur"


def test_debt_over_total_is_blocked_on_accept(qapp, monkeypatch):
    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(a[2]))
    d = CustomerPickerDialog(customers(), 84000)

    press(d, "9", "9", "9", "9", "9", "9")
    d._try_accept()

    assert warned and "katta" in warned[0]
    assert d.result() == 0              # dialog yopilmadi


def test_debt_zero_is_blocked(qapp, monkeypatch):
    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(a[2]))
    d = CustomerPickerDialog(customers(), 84000)
    d._edit("clear")

    d._try_accept()

    assert warned and "noldan katta" in warned[0]
