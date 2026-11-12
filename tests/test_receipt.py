from datetime import datetime
from types import SimpleNamespace

import pytest

from app.database.migrations import prepare_database
from app.services.product_service import ProductService
from app.services.receipt_service import ReceiptPrintError, ReceiptService
from app.services.sale_service import SaleService
from app.services.settings_service import SettingsService
from app.utils import receipt_render
from app.utils.receipt import BARCODE, NON_FISCAL_NOTE, build_receipt
from app.utils.receipt_render import PAPERS, render_receipt


def sale(**kw):
    base = dict(
        id=7, created_at=datetime(2026, 11, 12, 16, 30), status="completed",
        total_amount=100000.0, paid_amount=100000.0, change_amount=0.0,
        cash_amount=100000.0, card_amount=0.0, payment_method="cash",
        vat_total=0.0, fiscal_status="none",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def item(name="Non", qty=2, price=4000.0, vat_rate=0.0, vat_amount=0.0):
    return SimpleNamespace(
        product_name=name, quantity=qty, price=price, line_total=qty * price,
        vat_rate=vat_rate, vat_amount=vat_amount,
    )


def texts(receipt):
    return receipt.texts()


# ---------------- mazmun ----------------

def test_header_items_and_totals():
    r = build_receipt(
        sale(total_amount=8000, paid_amount=10000, change_amount=2000),
        [item()],
        {"store_name": "Vodiy Market", "store_address": "Farg'ona",
         "store_phone": "+998 90", "store_tin": "123456789", "store_legal_name": "VM MChJ"},
    )
    t = texts(r)

    assert "Vodiy Market" in t and "VM MChJ" in t and "STIR: 123456789" in t
    assert "#7" in t and "12.11.2026 16:30" in t
    assert "Non" in t and "2 × 4 000" in t and "8 000" in t
    assert "8 000 so'm" in t                       # JAMI
    assert "10 000 so'm" in t and "2 000 so'm" in t   # berildi / qaytim


def test_default_store_name_when_not_configured():
    assert "VMPOS" in texts(build_receipt(sale(), [item()], {}))


def test_non_fiscal_note_hidden_only_when_fiscalized():
    assert NON_FISCAL_NOTE in texts(build_receipt(sale(), [item()]))
    assert NON_FISCAL_NOTE in texts(build_receipt(sale(fiscal_status="pending"), [item()]))
    assert NON_FISCAL_NOTE not in texts(build_receipt(sale(fiscal_status="sent"), [item()]))


def test_vat_lines_grouped_by_rate():
    items = [
        item("A", 1, 112000, vat_rate=12, vat_amount=12000.0),
        item("B", 1, 11200, vat_rate=12, vat_amount=1200.0),
        item("C", 1, 1000, vat_rate=0, vat_amount=0.0),
    ]
    t = texts(build_receipt(sale(), items))

    assert "shu jumladan QQS 12%" in t and "13 200 so'm" in t
    assert not any("QQS 0%" in x for x in t)


def test_no_vat_line_without_vat():
    assert not any("QQS" in x for x in texts(build_receipt(sale(), [item()])))


def test_payment_variants():
    card = texts(build_receipt(sale(payment_method="card", card_amount=100000.0, cash_amount=0.0), [item()]))
    assert "Karta" in card and "Qaytim" not in card

    mixed = texts(build_receipt(sale(payment_method="mixed", cash_amount=60000.0, card_amount=40000.0), [item()]))
    assert "Naqd" in mixed and "Karta" in mixed and "60 000 so'm" in mixed and "40 000 so'm" in mixed

    debt = texts(build_receipt(sale(payment_method="debt", cash_amount=30000.0, card_amount=0.0), [item()]))
    assert "Nasiya (qarzga)" in debt and "70 000 so'm" in debt and "30 000 so'm" in debt


def test_refunded_status_is_marked():
    assert "** Qaytarilgan **" in texts(build_receipt(sale(status="refunded"), [item()]))
    assert "** Qisman qaytarilgan **" in texts(build_receipt(sale(status="partially_refunded"), [item()]))
    assert not any("**" in x for x in texts(build_receipt(sale(), [item()])))


def test_footer_and_barcode_options():
    r = build_receipt(sale(), [item()], options={"footer": "Rahmat!", "show_barcode": True})
    assert "Rahmat!" in texts(r)
    barcodes = [l for l in r.lines if l.kind == BARCODE]
    assert len(barcodes) == 1 and barcodes[0].text == "7"      # chek raqami

    r2 = build_receipt(sale(), [item()], options={"footer": "", "show_barcode": False})
    assert not [l for l in r2.lines if l.kind == BARCODE]
    assert "Xaridingiz uchun rahmat!" not in texts(r2)


# ---------------- chizish ----------------

def test_render_matches_thermal_dot_widths(qapp):
    r = build_receipt(sale(), [item()])

    assert render_receipt(r, "80").width() == PAPERS["80"][1] == 576
    assert render_receipt(r, "58").width() == PAPERS["58"][1] == 384


def test_render_is_not_blank_and_grows_with_content(qapp):
    one = render_receipt(build_receipt(sale(), [item()]), "80")
    many = render_receipt(build_receipt(sale(), [item(f"Mahsulot {i}") for i in range(10)]), "80")

    assert many.height() > one.height() + 9 * 40
    dark = sum(
        1 for x in range(0, one.width(), 3) for y in range(0, one.height(), 3)
        if one.pixelColor(x, y).value() < 100
    )
    assert dark > 100


def test_narrow_paper_wraps_long_names_into_taller_receipt(qapp):
    r = build_receipt(sale(), [item("Kungaboqar yog'i Oltin Vodiy premium 5 litr idish")])

    assert render_receipt(r, "58").height() > render_receipt(r, "80").height()


# ---------------- chop etish ----------------

def test_print_to_pdf_creates_valid_pdf(qapp, tmp_path):
    image = render_receipt(build_receipt(sale(), [item()]), "80", antialias=False)
    out = tmp_path / "chek.pdf"

    receipt_render.print_image(image, "80", pdf_path=out)

    data = out.read_bytes()
    assert data.startswith(b"%PDF") and len(data) > 500


def test_no_printers_installed_gives_clear_error(qapp, monkeypatch):
    monkeypatch.setattr(receipt_render, "available_printers", lambda: [])
    image = render_receipt(build_receipt(sale(), [item()]), "80")

    with pytest.raises(ReceiptPrintError, match="printer"):
        receipt_render.print_image(image, "80")


def test_unknown_printer_name_gives_clear_error(qapp, monkeypatch):
    monkeypatch.setattr(receipt_render, "available_printers", lambda: ["Boshqa printer"])
    image = render_receipt(build_receipt(sale(), [item()]), "80")

    with pytest.raises(ReceiptPrintError, match="Xprinter"):
        receipt_render.print_image(image, "80", printer_name="Xprinter XP-80")


# ---------------- servis ----------------

@pytest.fixture
def db(qapp):
    prepare_database()


def test_settings_defaults_round_trip_and_validation(db):
    s = ReceiptService.get_settings()
    assert (s["printer"], s["paper_mm"], s["auto_print"], s["show_barcode"]) == ("", "80", False, True)
    assert s["footer"] == "Xaridingiz uchun rahmat!"

    ReceiptService.save_settings({"printer": "POS-80", "paper_mm": "58", "footer": "", "auto_print": True, "show_barcode": False})
    s = ReceiptService.get_settings()
    assert (s["printer"], s["paper_mm"], s["auto_print"], s["show_barcode"]) == ("POS-80", "58", True, False)
    assert s["footer"] == ""                       # ataylab bo'sh — standartga qaytmaydi

    with pytest.raises(ValueError):
        ReceiptService.save_settings({"paper_mm": "70"})
    with pytest.raises(ValueError):
        ReceiptService.save_settings({"paper_mm": "80", "footer": "x" * 201})
    assert ReceiptService.get_settings()["paper_mm"] == "58"       # xato — o'zgarmadi


def make_real_sale():
    p = ProductService.create_product({
        "barcode": "", "name": "Non", "category": "X", "buy_price": 1, "sell_price": 112000,
        "unit": "dona", "quantity": 10, "min_quantity": 1, "description": "", "price_tiers": [],
        "ikpu_code": "1", "package_code": "1", "vat_rate": 12,
    })
    return SaleService.create_sale({p.id: {"product": p, "quantity": 2}}, "cash", 300000)


def test_build_and_print_real_sale_to_pdf(db, tmp_path):
    SettingsService.save_store_settings({"store_name": "Vodiy Market", "store_phone": "1", "store_address": "2"})
    sale_row = make_real_sale()

    receipt = ReceiptService.build_for_sale(sale_row.id)
    t = texts(receipt)
    assert "Vodiy Market" in t and "224 000 so'm" in t
    assert "shu jumladan QQS 12%" in t and "24 000 so'm" in t
    assert "76 000 so'm" in t                      # qaytim 300 000 - 224 000

    out = tmp_path / "real.pdf"
    ReceiptService.print_sale(sale_row.id, pdf_path=out)
    assert out.read_bytes().startswith(b"%PDF")


def test_unknown_sale_is_an_error(db):
    with pytest.raises(ValueError):
        ReceiptService.build_for_sale(9999)


def test_sample_receipt_builds_without_any_sale(db):
    t = texts(ReceiptService.build_sample())
    assert "Sinov mahsuloti 1" in t and NON_FISCAL_NOTE in t
