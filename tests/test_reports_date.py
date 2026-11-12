from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QDateEdit

from app.database.migrations import prepare_database

QSS = Path(__file__).resolve().parent.parent / "assets" / "styles" / "style.qss"


def test_reports_page_starts_on_today_not_year_2000(qapp):
    prepare_database()
    from app.ui.reports_page import ReportsPage

    page = ReportsPage()

    assert page.date_edit.date() == QDate.currentDate()
    assert page.date_edit.displayFormat() == "dd.MM.yyyy"


def test_date_text_fits_the_field_with_arrow(qapp):
    qapp.setStyleSheet(QSS.read_text(encoding="utf-8"))
    try:
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy")
        edit.setDate(QDate(2026, 12, 31))
        edit.ensurePolished()

        text_width = QFontMetrics(edit.font()).horizontalAdvance("31.12.2026")
        # chap padding 12 + strelka 32 + o'ng padding 6
        needed = text_width + 12 + 32 + 6

        assert edit.minimumSizeHint().width() >= needed
        assert edit.sizeHint().width() >= needed
        # Windows'da shrift/masshtab farqi uchun zaxira bilan: maydon
        # kamida 170 px (style.qss: QDateEdit min-width).
        assert edit.minimumSizeHint().width() >= 170
    finally:
        qapp.setStyleSheet("")
