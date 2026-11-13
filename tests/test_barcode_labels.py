from types import SimpleNamespace

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter

from app.utils import label_printing as lp
from app.utils.barcode_render import get_barcode_modules
from app.utils.scan_burst import IDLE_MS, ScanBurstParser

zxingcpp = pytest.importorskip("zxingcpp")
PIL_Image = pytest.importorskip("PIL.Image")

CODES = ["2000000000001", "4780001234567", "12345"]
SIZES = [(40, 30), (58, 40), (58, 30), (30, 20)]


def product(code):
    return SimpleNamespace(id=1, name="Non (tandir)", sell_price=4000.0, barcode=code)


def to_bilevel(image, threshold=140):
    gray = image.convertToFormat(QImage.Format_Grayscale8)
    pil = PIL_Image.frombytes(
        "L", (gray.width(), gray.height()), bytes(gray.constBits()), "raw", "L", gray.bytesPerLine(), 1
    )
    return pil.point(lambda v: 255 if v > threshold else 0, mode="L")


def render_label(code, size_mm, dpi):
    w = round(size_mm[0] / 25.4 * dpi)
    h = round(size_mm[1] / 25.4 * dpi)
    image = QImage(w, h, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    painter.setRenderHint(QPainter.TextAntialiasing, False)
    lp.paint_product_label(painter, QRectF(0, 0, w, h), product(code))
    painter.end()
    return image


def simple_decode(pil):
    """"Oddiy skaner": kuchli rejimlarsiz, qat'iy porog, faqat Code128."""

    results = zxingcpp.read_barcodes(
        pil, try_rotate=False, try_downscale=False, try_invert=False,
        binarizer=zxingcpp.Binarizer.FixedThreshold,
        formats=zxingcpp.BarcodeFormat.Code128,
    )
    return [r.text for r in results]


# ---------------- haqiqiy o'qilishi ----------------

@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("dpi", [203, 300])
def test_printed_label_barcode_is_readable_by_a_simple_decoder(qapp, size, code, dpi):
    pil = to_bilevel(render_label(code, size, dpi))

    assert code in simple_decode(pil), f"{size} mm {dpi} dpi {code} o'qilmadi"


# ---------------- geometriya ----------------

def paint_barcode_only(code, width_px=420, height_px=100):
    image = QImage(width_px + 40, height_px, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    painter.setRenderHint(QPainter.TextAntialiasing, False)
    lp._paint_barcode(painter, QRectF(20, 0, width_px, height_px), code)
    painter.end()
    return image


def dark_run_lengths(image, y):
    runs, current, count = [], None, 0

    for x in range(image.width()):
        dark = image.pixelColor(x, y).value() < 128
        if dark == current:
            count += 1
        else:
            if current is not None:
                runs.append((current, count))
            current, count = dark, 1
    runs.append((current, count))

    return runs


def test_quiet_zone_is_at_least_ten_modules_on_both_sides(qapp):
    code = "2000000000001"
    image = paint_barcode_only(code)
    y = 10                                            # chiziqlar sohasi (matndan yuqori)
    runs = dark_run_lengths(image, y)
    modules = len(get_barcode_modules(code))

    first_dark = next(i for i, (dark, _) in enumerate(runs) if dark)
    last_dark = max(i for i, (dark, _) in enumerate(runs) if dark)
    left = sum(n for _, n in runs[:first_dark])
    right = sum(n for _, n in runs[last_dark + 1:])
    bars = sum(n for _, n in runs[first_dark:last_dark + 1])
    module_px = bars / modules

    # rect chetlari (20 px) ham bo'sh joyga kiradi
    assert left - 20 >= 10 * module_px - 1             # standart: >= 10 modul (konstanta emas)
    assert right - 20 >= 10 * module_px - 1


def test_module_width_is_a_whole_number_of_device_pixels(qapp):
    image = paint_barcode_only("2000000000001")
    runs = [n for _, n in dark_run_lengths(image, 10)]
    runs = runs[1:-1]                                  # chetdagi bo'sh joylarsiz
    module = min(runs)

    assert module >= 2
    assert all(n % module == 0 for n in runs), f"notekis chiziqlar: {sorted(set(runs))}"


def test_density_helper_matches_real_sizes():
    assert lp.barcode_is_too_dense("2000000000001", 30) is True      # 30x20
    assert lp.barcode_is_too_dense("2000000000001", 40) is False
    assert lp.barcode_is_too_dense("2000000000001", 58) is False
    assert lp.barcode_is_too_dense("12345", 30) is False             # qisqa kod sig'adi
    assert lp.barcode_is_too_dense("", 40) is False                  # kod yo'q
    assert lp.barcode_module_mm("", 40) is None


# ---------------- dialog ogohlantirishi ----------------

def test_label_dialog_warns_only_when_the_size_is_too_small(qapp):
    from app.ui.label_print_dialog import LabelPrintDialog

    dialog = LabelPrintDialog([product("2000000000001")])
    dialog.size_combo.setCurrentText("58 x 40 mm")
    assert dialog.density_warning.isHidden()

    dialog.size_combo.setCurrentText("30 x 20 mm")
    assert not dialog.density_warning.isHidden()
    assert "juda zich" in dialog.density_warning.text()

    dialog.size_combo.setCurrentText("40 x 30 mm")
    assert dialog.density_warning.isHidden()


# ---------------- skaner portlashi ----------------

def test_fast_burst_with_enter_is_recognised_as_a_scanner():
    parser = ScanBurstParser()
    t = 1000

    for ch in "2000000000001":
        assert parser.feed_char(ch, t) is None
        t += 2

    record = parser.feed_suffix("Enter", t)

    assert record.text == "2000000000001" and record.suffix == "Enter"
    assert record.looks_like_scanner and record.ms_per_char <= 3


def test_slow_typing_is_not_a_scanner():
    parser = ScanBurstParser()
    t = 0

    for ch in "123456":
        parser.feed_char(ch, t)
        t += 180

    record = parser.feed_suffix("Enter", t)

    assert record.text == "123456" and not record.looks_like_scanner


def test_tab_suffix_and_no_suffix_are_reported():
    parser = ScanBurstParser()

    for i, ch in enumerate("4780001234567"):
        parser.feed_char(ch, i)
    assert parser.feed_suffix("Tab", 20).suffix == "Tab"

    for i, ch in enumerate("999000"):
        parser.feed_char(ch, 1000 + i)
    assert parser.flush(1005 + IDLE_MS - 1) is None                  # hali erta
    record = parser.flush(1005 + IDLE_MS + 1)
    assert record.text == "999000" and record.suffix == ""


def test_new_burst_after_a_pause_finishes_the_previous_one():
    parser = ScanBurstParser()
    parser.feed_char("1", 0)
    parser.feed_char("2", 5)

    finished = parser.feed_char("9", 5 + IDLE_MS + 50)

    assert finished.text == "12"
    assert parser.feed_suffix("Enter", 400).text == "9"


def test_enter_without_chars_is_ignored():
    assert ScanBurstParser().feed_suffix("Enter", 0) is None
