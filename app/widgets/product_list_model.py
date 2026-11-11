from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

ProductRole = Qt.UserRole + 1
# Mahsulotning korzinadagi miqdori (0 — korzinada yo'q).
CartQtyRole = Qt.UserRole + 2


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

        if role == Qt.DisplayRole:
            return product.name

        return None
