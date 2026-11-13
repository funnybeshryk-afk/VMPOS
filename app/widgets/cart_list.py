from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.utils import motion
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
        self._flash = 0.0

        self.setObjectName("cartRow")
        self.setProperty("selected", "true" if selected else "false")
        self.setFixedHeight(_ROW_HEIGHT)

        product = item["product"]
        quantity = item["quantity"]
        unit_price = item["unit_price"]
        weight = is_weight_unit(product.unit)

        layout = QVBoxLayout(self)
        # Balandlik animatsiyasi paytida (0 dan o'sadi) tarkibning
        # minimal o'lchami qatorni ushlab turmasligi uchun.
        layout.setSizeConstraint(QLayout.SetNoConstraint)
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
            minus.setFocusPolicy(Qt.NoFocus)
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
        self.quantity_button.setFocusPolicy(Qt.NoFocus)
        self.quantity_button.setToolTip("Miqdorni kiritish")
        self.quantity_button.clicked.connect(
            lambda: self.editRequested.emit(self._product_id)
        )
        bottom_row.addWidget(self.quantity_button)

        if not weight:
            plus = QPushButton("+")
            plus.setObjectName("qtyPlus")
            plus.setCursor(Qt.PointingHandCursor)
            plus.setFocusPolicy(Qt.NoFocus)
            plus.clicked.connect(
                lambda: self.changeRequested.emit(self._product_id, 1)
            )
            bottom_row.addWidget(plus)

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

    def set_flash(self, value):
        self._flash = value
        self.update()

    def flash(self):
        """Miqdor o'zgardi — qator qisqa izumrud yonib o'chadi."""

        if not motion.is_enabled():
            return

        animation = QVariantAnimation(self)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setDuration(motion.DURATION_FLASH_MS)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.valueChanged.connect(self.set_flash)
        animation.finished.connect(lambda: self.set_flash(0.0))
        animation.start()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._flash > 0.001:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(5, 150, 105, int(60 * self._flash)))
            painter.drawRoundedRect(self.rect(), 14, 14)
            painter.end()

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
        self._quantities = {}

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
        previous_quantities = self._quantities

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

        # Animatsiyalar: yangi qator chiqadi, miqdori o'zgargani yonadi.
        # Mantiq (yuqorida) animatsiyaga bog'liq emas.
        if motion.is_enabled():
            for product_id, row in self._rows.items():
                if product_id not in previous_quantities:
                    self._animate_in(row)
                elif previous_quantities[product_id] != items[product_id]["quantity"]:
                    row.flash()

        self._quantities = {
            product_id: item["quantity"] for product_id, item in items.items()
        }

    def _animate_in(self, row):
        """Yangi qator: balandligi 0 dan o'sadi va xiralikdan chiqadi."""

        effect = QGraphicsOpacityEffect(row)
        effect.setOpacity(0.0)
        row.setGraphicsEffect(effect)
        row.setMinimumHeight(0)
        row.setMaximumHeight(0)

        group = QParallelAnimationGroup(row)

        height = QPropertyAnimation(row, b"maximumHeight", group)
        height.setStartValue(0)
        height.setEndValue(_ROW_HEIGHT)

        fade = QPropertyAnimation(effect, b"opacity", group)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)

        for animation in (height, fade):
            animation.setDuration(motion.DURATION_ROW_MS)
            animation.setEasingCurve(QEasingCurve.OutCubic)

        # Yangi qator ro'yxat oxirida o'sayotganda ko'rinib turishi uchun.
        height.valueChanged.connect(
            lambda _value: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            )
        )
        group.finished.connect(lambda: self._finish_animate_in(row))
        group.start()

    def _finish_animate_in(self, row):
        row.setGraphicsEffect(None)
        row.setFixedHeight(_ROW_HEIGHT)
