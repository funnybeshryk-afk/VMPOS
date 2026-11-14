from app.widgets.app_status_bar import (
    AppStatusBar,
    ScanActivityMonitor,
    printer_state,
)


def test_printer_state_saved_present():
    assert printer_state("XP-80", ["XP-80"], "") == ("Tayyor", "success")


def test_printer_state_saved_missing_is_danger():
    assert printer_state("XP-80", ["Other"], "Other") == ("Topilmadi", "danger")


def test_printer_state_default_used():
    assert printer_state("", ["A", "B"], "B") == ("Tayyor", "success")


def test_printer_state_none_means_pdf():
    assert printer_state("", [], "") == ("PDF", "neutral")
    assert printer_state("", ["A"], "") == ("PDF", "neutral")


def _monitor(step_ms):
    seen = []
    t = {"now": 0}
    mon = ScanActivityMonitor(seen.append, clock=lambda: t["now"])

    def type_text(text, suffix="Enter"):
        for ch in text:
            mon.handle_key(ch)
            t["now"] += step_ms
        mon.handle_key("", suffix)
        t["now"] += 1000

    return seen, type_text


def test_fast_burst_counts_as_scan():
    seen, type_text = _monitor(5)
    type_text("2000000000001")
    assert [r.text for r in seen] == ["2000000000001"]


def test_slow_typing_is_not_a_scan():
    seen, type_text = _monitor(150)
    type_text("2000000000001")
    assert seen == []


def test_status_bar_scan_updates_badge(qapp):
    bar = AppStatusBar(install_scan_monitor=False)
    assert bar.scanner_badge.text() == "Kutilmoqda"

    class R:
        text = "123"
        ms_per_char = 7.0

    bar.note_scan(R())
    assert bar.scanner_badge.text().startswith("Skan ")
    assert "123" in bar.scanner_badge.toolTip()
    assert bar.scanner_badge.objectName() == "badgeSuccess"
    bar.deleteLater()
