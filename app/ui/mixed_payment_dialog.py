from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.ui.touch_dialog import TouchDialog
from app.utils.amount_buffer import AmountBuffer
from app.utils.formatters import format_money
from app.widgets.numpad import AmountField, NumPad

_TOLERANCE = 0.01


class MixedPaymentDialog(TouchDialog):
    """Naqd va karta o'rtasida bo'lingan to'lov — sensorli.

    Ikkita katta maydon: Naqd va Karta. Bosilgan maydon faol (izumrud
    ramka), raqamli blok shuni tahrirlaydi; ikkinchisi avtomatik
    "qolgan summa"ga o'rnatiladi — shuning uchun summalar jamiga
    deyarli har doim mos keladi va kassir bitta qiymat kiritadi.
    Qaytim tushunchasi yo'q: karta orqali qaytim berib bo'lmaydi.

    Imzo avvalgidek: MixedPaymentDialog(total, parent),
    get_payment_data() -> (cash, card).
    """

    def __init__(self, total_amount, parent=None):
        super().__init__("Aralash to'lov", parent, min_width=540)

        self.total_amount = total_amount

        self._buffers = {
            "cash": AmountBuffer(allow_decimal=True, max_decimals=2),
            "card": AmountBuffer(allow_decimal=True, max_decimals=2),
        }
        self._active = "cash"

        # Boshlang'ich taklif: butun summa naqdda — kassir kartaga
        # tushadigan qismini ajratib kiritadi.
        self._buffers["cash"].set_value(total_amount)
        self._buffers["card"].set_value(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(12)

        layout.addWidget(self._build_total_box())

        self._fields = {
            "cash": AmountField("Naqd pul", "so'm"),
            "card": AmountField("Karta", "so'm"),
        }

        for key, field in self._fields.items():
            field.clicked.connect(lambda k=key: self._activate(k))
            layout.addWidget(field)

        self._hint = QLabel()
        self._hint.setObjectName("entryHint")
        layout.addWidget(self._hint)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.addWidget(self.make_chip("Hammasi naqd", lambda: self._split(1)))
        chips.addWidget(self.make_chip("50 / 50", lambda: self._split(0.5)))
        chips.addWidget(self.make_chip("Hammasi karta", lambda: self._split(0)))
        layout.addLayout(chips)

        pad = NumPad(left_key="000")
        self.connect_numpad(pad)
        layout.addWidget(pad)

        layout.addLayout(self.build_footer("Tasdiqlash"))

        self._refresh()

    def _build_total_box(self):
        box = QFrame()
        box.setObjectName("totalBox")
        box.setFixedHeight(84)

        caption = QLabel("Jami")
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

    # ---- TouchDialog ---------------------------------------------

    def active_buffer(self):
        return self._buffers[self._active]

    def buffer_changed(self):
        # Faol maydon yozildi -> ikkinchisi "qolgan summa".
        other = "card" if self._active == "cash" else "cash"
        entered = self._buffers[self._active].value()

        self._buffers[other].set_value(max(self.total_amount - entered, 0))
        self._refresh()

    # ---- ichki ----------------------------------------------------

    def _refresh(self):
        cash = self._buffers["cash"].value()
        card = self._buffers["card"].value()
        remaining = self.total_amount - (cash + card)

        for key, field in self._fields.items():
            buffer = self._buffers[key]

            # Faol maydon yozilayotgan matnni (masalan "12,"), faol
            # bo'lmagani esa tayyor qiymatni ko'rsatadi.
            field.set_text(buffer.display())
            field.set_active(key == self._active)

        if abs(remaining) <= _TOLERANCE:
            self._hint.setText("Summalar jamga mos")
            state = "ok"
        elif remaining > 0:
            self._hint.setText(f"Yetishmayapti: {format_money(remaining)} so'm")
            state = "bad"
        else:
            self._hint.setText(f"Ortiqcha: {format_money(-remaining)} so'm")
            state = "bad"

        self._hint.setProperty("state", state)
        self._hint.style().unpolish(self._hint)
        self._hint.style().polish(self._hint)

        for field in self._fields.values():
            field.set_state(state if state == "bad" else "ok")

        self.ok_button.setEnabled(state == "ok" and self.total_amount > 0)

    def _activate(self, key):
        if key == self._active:
            return

        self._active = key
        # Tayyor qiymat ustiga birinchi raqam uni almashtiradi.
        self._buffers[key].set_value(self._buffers[key].value())
        self._refresh()

    def _split(self, cash_share):
        cash = round(self.total_amount * cash_share, 2)

        self._buffers["cash"].set_value(cash)
        self._buffers["card"].set_value(self.total_amount - cash)
        self._active = "cash"
        self._refresh()

    def get_payment_data(self):
        return (
            self._buffers["cash"].value(),
            self._buffers["card"].value(),
        )
