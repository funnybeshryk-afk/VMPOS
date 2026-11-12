from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.ui.touch_dialog import TouchDialog
from app.utils.amount_buffer import AmountBuffer
from app.utils.formatters import format_money
from app.widgets.numpad import AmountField, NumPad

_TOLERANCE = 0.01

# O'zbekiston qog'oz pullari: kassir mijoz bergan puldagi tugmani bosadi.
_NOTE_CHIPS = (20_000, 50_000, 100_000, 200_000)


class PaymentDialog(TouchDialog):
    """Naqd/karta to'lovi — sensorli: yirik "Qabul qilindi", qaytim,
    "Aniq" va qog'oz pul tugmalari, raqamli blok.

    Imzo avvalgidek: PaymentDialog(total, payment_method=None, parent)
    va get_payment_data() -> (method, paid_amount).
    """

    def __init__(self, total_amount, payment_method=None, parent=None):
        super().__init__("To'lov", parent, min_width=560)

        self.total_amount = total_amount
        self.fixed_payment_method = payment_method

        self._buffer = AmountBuffer(allow_decimal=True, max_decimals=2)
        # Boshlang'ich taklif — aniq summa (avvalgidek): mijoz aniq
        # to'lasa, kassir faqat tasdiqlaydi.
        self._buffer.set_value(total_amount)

        self._is_card = payment_method == "card"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(12)

        self.cash_tab = None
        self.card_tab = None

        if payment_method is None:
            layout.addLayout(self._build_tabs())

        layout.addWidget(self._build_total_box())

        self._received = AmountField("Qabul qilindi", "so'm")
        self._received.set_active(True)
        layout.addWidget(self._received)

        self._change = QLabel()
        self._change.setObjectName("changeLabel")
        layout.addWidget(self._change)

        self._chips_row = QHBoxLayout()
        self._chips_row.setSpacing(8)
        self._chips = [self.make_chip("Aniq", self._exact)]

        for amount in _NOTE_CHIPS:
            self._chips.append(
                self.make_chip(
                    f"+{format_money(amount)}",
                    lambda _=False, a=amount: self._add_note(a),
                )
            )

        for chip in self._chips:
            self._chips_row.addWidget(chip)

        layout.addLayout(self._chips_row)

        self._pad = NumPad(left_key="000")
        self.connect_numpad(self._pad)
        layout.addWidget(self._pad)

        layout.addLayout(self.build_footer("Tasdiqlash"))

        self.buffer_changed()

    # ---- qurilish ---------------------------------------------------

    def _build_total_box(self):
        box = QFrame()
        box.setObjectName("totalBox")
        box.setFixedHeight(84)

        caption = QLabel("To'lash kerak")
        caption.setObjectName("cartTotalCaption")

        amount = QLabel(
            f"{format_money(self.total_amount)} "
            "<span style='font-size:18px;font-weight:500;"
            "color:#a8a29e'>so'm</span>"
        )
        amount.setObjectName("cartTotalAmount")
        amount.setTextFormat(Qt.RichText)

        row = QHBoxLayout(box)
        row.setContentsMargins(24, 0, 24, 0)
        row.addWidget(caption)
        row.addStretch()
        row.addWidget(amount)

        return box

    def _build_tabs(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        group = QButtonGroup(self)
        group.setExclusive(True)

        self.cash_tab = self._tab("Naqd pul", checked=True)
        self.card_tab = self._tab("Karta")

        for tab in (self.cash_tab, self.card_tab):
            group.addButton(tab)
            row.addWidget(tab)

        row.addStretch()

        self.cash_tab.toggled.connect(self._on_method_changed)

        return row

    def _tab(self, text, checked=False):
        tab = QPushButton(text)
        tab.setObjectName("tabButton")
        tab.setCheckable(True)
        tab.setChecked(checked)
        tab.setFocusPolicy(Qt.NoFocus)
        tab.setCursor(Qt.PointingHandCursor)

        return tab

    # ---- TouchDialog ------------------------------------------------

    def active_buffer(self):
        return None if self._is_card else self._buffer

    def buffer_changed(self):
        if self._is_card:
            self._received.set_text(format_money(self.total_amount))
            self._change.setText("Karta: butun summa yechiladi")
            self._set_change_state("ok")
            self.ok_button.setEnabled(True)
        else:
            paid = self._buffer.value()
            difference = paid - self.total_amount
            self._received.set_text(self._buffer.display())

            if difference >= -_TOLERANCE:
                self._change.setText(
                    f"Qaytim: {format_money(max(difference, 0))} so'm"
                )
                self._set_change_state("ok")
                self._received.set_state("ok")
                self.ok_button.setEnabled(True)
            else:
                self._change.setText(
                    f"Yetmayapti: {format_money(-difference)} so'm"
                )
                self._set_change_state("bad")
                self._received.set_state("bad")
                self.ok_button.setEnabled(False)

        enabled = not self._is_card
        self._pad.setEnabled(enabled)

        for chip in self._chips:
            chip.setEnabled(enabled)

        if self._is_card:
            self._received.set_state("ok")

    def _set_change_state(self, state):
        self._change.setProperty("state", state)
        self._change.style().unpolish(self._change)
        self._change.style().polish(self._change)

    # ---- tugmalar ---------------------------------------------------

    def _on_method_changed(self, cash_checked):
        self._is_card = not cash_checked
        self.buffer_changed()

    def _exact(self):
        self._buffer.set_value(self.total_amount)
        self.buffer_changed()

    def _add_note(self, amount):
        self._buffer.add(amount)
        self.buffer_changed()

    # ---- natija -----------------------------------------------------

    def get_payment_data(self):
        if self._is_card:
            return "card", self.total_amount

        return "cash", self._buffer.value()
