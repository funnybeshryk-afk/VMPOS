from types import SimpleNamespace

from PySide6.QtCore import QEvent, QObject
from PySide6.QtTest import QTest

from app.utils import motion
from app.widgets.product_grid import ProductGrid


class _Paints(QObject):
    def __init__(self):
        super().__init__()
        self.areas = []

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Paint:
            rect = event.rect()
            self.areas.append(rect.width() * rect.height())

        return False


def _products(count):
    return [
        SimpleNamespace(
            id=i, name=f"P{i}", sell_price=1000 + i, barcode="", unit="dona",
            quantity=10, min_quantity=1, image_path=None, category="K",
        )
        for i in range(1, count + 1)
    ]


def test_flash_repaints_only_the_flashing_card(qapp, monkeypatch):
    monkeypatch.setattr(motion, "is_enabled", lambda: True)

    grid = ProductGrid()
    grid.resize(760, 700)
    grid.set_products(_products(12))
    grid.show()
    QTest.qWait(100)

    paints = _Paints()
    grid.viewport().installEventFilter(paints)

    grid.flash_product(3)
    QTest.qWait(420)  # vspishka davomiyligidan (260 ms) uzunroq

    viewport_area = grid.viewport().width() * grid.viewport().height()

    assert paints.areas, "vspishka paytida hech narsa chizilmadi"
    # Hech bir kadrda butun panjara qayta chizilmaydi.
    assert max(paints.areas) < viewport_area * 0.5
    assert not grid._flash_timer.isActive()

    grid.close()
