from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListView

from app.widgets.product_card_delegate import CARD_SIZE, ProductCardDelegate
from app.widgets.product_list_model import ProductListModel, ProductRole

_SPACING = 6


class ProductGrid(QListView):
    """Sotuv katalogining panjara (grid) ko'rinishi — virtuallashtirilgan.

    QListView + model + delegate: 1000+ mahsulot bo'lsa ham faqat
    ekranda ko'rinadigan (+ ozgina zaxira) qatorlar uchun paint()
    chaqiriladi. IconMode + ResizeMode.Adjust — oyna kengligi
    o'zgarganda ustunlar sonini Qt o'zi qayta hisoblaydi, qo'lda
    reflow() yozishning hojati yo'q (avvalgi QGridLayout asosidagi
    versiyada bu qo'lda qilingan edi).
    """

    productClicked = Signal(int)

    def __init__(self):
        super().__init__()

        self.setObjectName("productGridView")

        self._model = ProductListModel(self)
        self.setModel(self._model)

        self.setItemDelegate(ProductCardDelegate(self))

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setSpacing(_SPACING)
        self.setGridSize(CARD_SIZE)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QListView.NoFrame)
        self.viewport().setObjectName("productGridViewport")

        self.clicked.connect(self._on_clicked)

    def set_products(self, products):
        self._model.set_products(products)

    def _on_clicked(self, index):
        product = index.data(ProductRole)

        if product is not None:
            self.productClicked.emit(product.id)
