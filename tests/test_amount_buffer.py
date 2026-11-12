import pytest

from app.utils.amount_buffer import AmountBuffer


def typed(buffer, text):
    for ch in text:
        if ch == ",":
            buffer.press_decimal()
        else:
            buffer.press_digit(ch)


def test_empty_is_zero():
    b = AmountBuffer()
    assert b.value() == 0 and b.display() == "0"


def test_digits_accumulate_and_group():
    b = AmountBuffer()
    typed(b, "1250000")
    assert b.value() == 1250000
    assert b.display() == "1 250 000"


def test_no_leading_zeros():
    b = AmountBuffer()
    typed(b, "007")
    assert b.raw() == "7"
    b.clear(); typed(b, "0"); typed(b, "0")
    assert b.raw() == "0"


def test_first_digit_replaces_preset_value():
    b = AmountBuffer()
    b.set_value(84000)
    assert b.display() == "84 000"
    typed(b, "1")
    assert b.value() == 1            # tayyor summa almashdi


def test_backspace_trims_preset_instead_of_replacing():
    b = AmountBuffer()
    b.set_value(100000)
    b.backspace()
    assert b.value() == 10000
    typed(b, "5")                    # endi oddiy yozish: 100005? yo'q — 10000 + 5
    assert b.value() == 100005


def test_triple_zero_multiplies_but_never_on_preset_or_empty():
    b = AmountBuffer()
    b.press_zeros()
    assert b.raw() == ""             # bo'sh ustiga nol yig'ilmaydi
    typed(b, "50"); b.press_zeros()
    assert b.value() == 50000
    b.set_value(84000); b.press_zeros()
    assert b.value() == 84000        # tayyor summani buzmaydi


def test_decimal_only_when_allowed_and_only_once():
    b = AmountBuffer(allow_decimal=False)
    typed(b, "5,5")
    assert b.value() == 55           # vergul e'tiborsiz

    d = AmountBuffer(allow_decimal=True, max_decimals=3)
    typed(d, "2,5,5")
    assert d.raw() == "2,55"
    assert d.value() == pytest.approx(2.55)


def test_decimal_places_are_limited():
    d = AmountBuffer(allow_decimal=True, max_decimals=3)
    typed(d, "1,23456")
    assert d.raw() == "1,234"


def test_leading_decimal_gets_zero():
    d = AmountBuffer(allow_decimal=True)
    d.press_decimal(); typed(d, "5")
    assert d.raw() == "0,5" and d.value() == 0.5


def test_add_chip_accumulates_notes():
    b = AmountBuffer()
    b.set_value(0)
    b.add(100000); b.add(50000)
    assert b.value() == 150000


def test_integer_digit_limit():
    b = AmountBuffer(max_int_digits=4)
    typed(b, "123456")
    assert b.raw() == "1234"


def test_set_value_without_decimals_drops_fraction():
    b = AmountBuffer(allow_decimal=False)
    b.set_value(12.7)
    assert b.value() == 12


def test_set_value_keeps_decimals_when_allowed():
    d = AmountBuffer(allow_decimal=True)
    d.set_value(2.5)
    assert d.display() == "2,5"


def test_note_chip_replaces_untouched_prefill_then_accumulates():
    b = AmountBuffer()
    b.set_value(84000)               # dialog ochilganda "jami" qo'yilgan
    b.add(100000)
    assert b.value() == 100000       # 184 000 emas!
    b.add(50000)
    assert b.value() == 150000
