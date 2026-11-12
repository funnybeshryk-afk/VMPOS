from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.utils.formatters import format_money, format_quantity
from app.utils.units import is_weight_unit
from app.widgets.badge import StatusBadge

_ROW_HEIGHT = 88

class _ElidedLabel(QLabel):
    """Sig'maydigan matnni "…" bilan qisqartiradigan yorliq (to'liq
    matn tooltip'da) — oddiy QLabel uzun nomni jimgina kesib tashlaydi."""

    def __init__(self, text):
        super().__init__()

        self._full_text = text or ""
        self.setToolTip(self._full_text)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self._apply()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply()

    def _apply(self):
        self.setText(
            self.fontMetrics().elidedText(
                self._full_text, Qt.ElideRight, max(0, self.width())
            )
        )


class _CartRow(QFrame):
    """Korzinadagi bitta qator: nom/narx, miqdor stepperi, jami summa.

    Qatorning o'zini bosish — uni tanlaydi (Delete bilan o'chirish
    uchun, eski jadvaldagi qator tanlovi kabi). Barmoq uchun hamma
    tugma 40x40.
    """

    selectRequested = Signal(int)
    changeRequested = Signal(int, int)  # product_id, +1 / -1
    editRequested = Signal(int)

    def __init__(self, product_id, item, selected):
        super().__init__()

        self._product_id = product_id

        self.setObjectName("cartRow")
        self.setProperty("selected", "true" if selected else "false")
        self.setFixedHeight(_ROW_HEIGHT)

        product = item["product"]
        quantity = item["quantity"]
        unit_price = item["unit_price"]
        weight = is_weight_unit(product.unit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 14, 8)
        layout.setSpacing(2)

        # 1-qator: nom (joyga qarab qisqaradi) va qator jami summasi.
        name_label = _ElidedLabel(product.name)
        name_label.setObjectName("cartRowName")

        total_label = QLabel(format_money(unit_price * quantity))
        total_label.setObjectName("cartRowTotal")
        total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.addWidget(name_label, 1)
        top_row.addWidget(total_label)

        # 2-qator: birlik narxi (+ "Optom") va miqdor stepperi.
        price_label = QLabel(f"{format_money(unit_price)} so'm")
        price_label.setObjectName("cartRowPrice")

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)
        bottom_row.addWidget(price_label)

        if item["is_wholesale"]:
            bottom_row.addWidget(StatusBadge("Optom", "success"))

        bottom_row.addStretch()

        if not weight:
            minus = QPushButton("–")
            minus.setObjectName("qtyMinus")
            minus.setCursor(Qt.PointingHandCursor)
            minus.clicked.connect(
                lambda: self.changeRequested.emit(self._product_id, -1)
            )
            bottom_row.addWidget(minus)

        quantity_text = format_quantity(quantity)

        if weight:
            quantity_text += f" {product.unit.strip()}"

        self.quantity_button = QPushButton(quantity_text)
        self.quantity_button.setObjectName("qtyValue")
        self.quantity_button.setCursor(Qt.PointingHandCursor)
        self.quantity_button.setToolTip("Miqdorni kiritish")
        self.quantity_button.clicked.connect(
            lambda: self.editRequested.emit(self._product_id)
        )
        bottom_row.addWidget(self.quantity_button)

        if not weight:
            plus = QPushButton("+")
            plus.setObjectName("qtyPlus")
            plus.setCursor(Qt.PointingHandCursor)
            plus.clicked.connect(
                lambda: self.changeRequested.emit(self._product_id, 1)
            )
            bottom_row.addWidget(plus)

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

    def mousePressEvent(self, event):
        self.selectRequested.emit(self._product_id)
        super().mousePressEvent(event)


class CartList(QScrollArea):
    """Korzina ro'yxati — qator-kartochkalar (avvalgi jadval o'rniga).

    "Ko'r" vidjet: ma'lumotni SalePage beradi (set_items), o'zgartirish
    so'rovlarini signal sifatida qaytaradi — narx/qoldiq/optom qoidalari
    sahifada qoladi, shu yerga ko'chmaydi.
    """

    changeRequested = Signal(int, int)
    editRequested = Signal(int)

    def __init__(self):
        super().__init__()

        self.setObjectName("cartScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viewport().setObjectName("cartScrollViewport")

        self._content = QWidget()
        self._content.setObjectName("cartListContent")

        self._rows_layout = QVBoxLayout(self._content)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.setSpacing(8)
        self._rows_layout.addStretch()

        self.setWidget(self._content)

        self._selected_id = None
        self._rows = {}

    def selected_product_id(self):
        return self._selected_id

    def select(self, product_id):
        self._selected_id = product_id

        for row_id, row in self._rows.items():
            row.setProperty(
                "selected", "true" if row_id == product_id else "false"
            )
            row.style().unpolish(row)
            row.style().polish(row)

    def set_items(self, items):
        """items: {product_id: {product, quantity, unit_price, is_wholesale}}."""

        scroll_value = self.verticalScrollBar().value()

        for row in self._rows.values():
            self._rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()

        self._rows = {}

        if self._selected_id not in items:
            self._selected_id = None

        for index, (product_id, item) in enumerate(items.items()):
            row = _CartRow(
                product_id, item, product_id == self._selected_id
            )
            row.selectRequested.connect(self.select)
            row.changeRequested.connect(self.changeRequested)
            row.editRequested.connect(self.editRequested)

            self._rows_layout.insertWidget(index, row)
            self._rows[product_id] = row

        self.verticalScrollBar().setValue(scroll_value)
