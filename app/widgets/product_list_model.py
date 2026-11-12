import time

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from app.utils import motion

ProductRole = Qt.UserRole + 1
# Mahsulotning korzinadagi miqdori (0 — korzinada yo'q).
CartQtyRole = Qt.UserRole + 2
# Kartochka "vspishka" intensivligi: 1.0 -> 0.0 (motion.DURATION_FLASH_MS ichida).
FlashRole = Qt.UserRole + 3


class ProductListModel(QAbstractListModel):
    """Sotuv katalogi uchun yengil ro'yxat modeli.

    Faqat ProductCardDelegate.paint() o'qiydigan xom Product
    obyektini saqlaydi. QListView shu model ustida virtuallashgan
    holda ishlaydi: 1000+ mahsulot bo'lsa ham, bir vaqtning o'zida
    faqat ekranda ko'rinadigan (+ ozgina zaxira) qatorlar uchun
    delegate.paint() chaqiriladi — avvalgi QWidget asosidagi versiyada
    esa BARCHA mahsulot uchun to'liq vidjet daraxti darhol yaratilar
    edi.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._products = []
        self._cart_quantities = {}
        self._flash_started = {}

    def flash(self, product_id):
        """Mahsulot korzinaga qo'shildi — kartochka qisqa yonib o'chadi."""

        if motion.is_enabled():
            self._flash_started[product_id] = time.monotonic()

    def flash_intensity(self, product_id):
        started = self._flash_started.get(product_id)

        if started is None:
            return 0.0

        elapsed_ms = (time.monotonic() - started) * 1000

        if elapsed_ms >= motion.DURATION_FLASH_MS:
            del self._flash_started[product_id]
            return 0.0

        remaining = 1 - elapsed_ms / motion.DURATION_FLASH_MS

        return remaining * remaining  # tez so'nadi (ease-out)

    def has_active_flash(self):
        # Tugagan vspishkalarni ham tozalaydi.
        for product_id in list(self._flash_started):
            self.flash_intensity(product_id)

        return bool(self._flash_started)

    def set_cart_quantities(self, quantities):
        """{product_id: miqdor}. Faqat o'zgargan bo'lsa qayta chizadi."""

        quantities = dict(quantities)

        if quantities == self._cart_quantities:
            return

        self._cart_quantities = quantities

        if self._products:
            self.dataChanged.emit(
                self.index(0),
                self.index(len(self._products) - 1),
                [CartQtyRole],
            )

    def set_products(self, products):
        self.beginResetModel()
        self._products = list(products)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0

        return len(self._products)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        product = self._products[index.row()]

        if role == ProductRole:
            return product

        if role == CartQtyRole:
            return self._cart_quantities.get(product.id, 0)

        if role == FlashRole:
            return self.flash_intensity(product.id)

        if role == Qt.DisplayRole:
            return product.name

        return None
