from pathlib import Path

from PySide6.QtCore import Qt

from app.widgets.app_status_bar import AppStatusBar


def test_status_bar_paints_its_dark_background_from_qss(qapp):
    # Qt'da QWidget'dan meros olingan klass QSS fonini WA_StyledBackground'siz
    # chizmaydi — holat qatori fonsiz/chegarasiz qolgan edi.
    qss = (Path(__file__).resolve().parent.parent / "assets" / "styles" / "style.qss").read_text(encoding="utf-8")
    previous = qapp.styleSheet()
    qapp.setStyleSheet(qss)

    try:
        bar = AppStatusBar()
        bar.resize(600, 40)
        bar.show()
        qapp.processEvents()

        assert bar.testAttribute(Qt.WA_StyledBackground)

        image = bar.grab().toImage()
        # Matn bo'lmagan joy (o'rtada) — "ink" #1c1917, oq/krem emas.
        color = image.pixelColor(300, 20)
        assert color.red() < 60 and color.green() < 60 and color.blue() < 60

        bar.close()
    finally:
        qapp.setStyleSheet(previous)
