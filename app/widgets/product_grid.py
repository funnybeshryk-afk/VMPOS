from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QAbstractItemView, QListView

from app.widgets.product_card_delegate import CARD_SIZE, ProductCardDelegate
from app.widgets.product_list_model import ProductListModel, ProductRole

_SPACING = 6

# Kartochka eni kengligi shu minimaldan boshlab ustunlarga bo'linadi:
# qator har doim to'liq to'ladi (o'ng tomonda bo'sh joy qolmaydi).
_MIN_CARD_WIDTH = 232


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

        # Vspishka davomida (<= ~260 ms) viewport'ni ~60 kadr/s qayta
        # chizadi; tugagach taymer to'xtaydi (bo'sh turganda hech narsa
        # ishlamaydi).
        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(16)
        self._flash_timer.timeout.connect(self._tick_flash)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_columns()

    def _fit_columns(self):
        """Mavjud kenglikka sig'adigan ustunlar sonini hisoblab, har
        kartochkaga teng kenglik beradi. Balandlik qat'iy."""

        available = self.viewport().width() - 2 * _SPACING

        if available <= 0:
            return

        columns = max(1, available // _MIN_CARD_WIDTH)
        cell_width = available // columns

        if self.gridSize().width() != cell_width:
            self.setGridSize(QSize(cell_width, CARD_SIZE.height()))

    def set_products(self, products):
        self._model.set_products(products)

    def set_cart_quantities(self, quantities):
        self._model.set_cart_quantities(quantities)

    def flash_product(self, product_id):
        self._model.flash(product_id)

        if self._model.has_active_flash() and not self._flash_timer.isActive():
            self._flash_timer.start()

    def _tick_flash(self):
        self.viewport().update()

        if not self._model.has_active_flash():
            self._flash_timer.stop()

    def _on_clicked(self, index):
        product = index.data(ProductRole)

        if product is not None:
            self.productClicked.emit(product.id)
