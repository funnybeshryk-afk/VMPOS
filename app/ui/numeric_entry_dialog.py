from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from app.ui.touch_dialog import TouchDialog
from app.utils.amount_buffer import AmountBuffer
from app.utils.formatters import format_money, format_quantity
from app.widgets.numpad import AmountField, NumPad
from app.i18n import tr

_EPSILON = 1e-9


class NumericEntryDialog(TouchDialog):
    """Bitta son kiritish: miqdor yoki og'irlik. Katta raqamli blok,
    tezkor qiymatlar (0,5 / 1 / 2 / 5 kg), real vaqtda tekshiruv
    (eng kami / qoldiqdan oshmasin) va jami summa.

    price_for(qty) -> birlik narxi (optom hisobga olingan); berilmasa
    jami ko'rsatilmaydi.
    """

    def __init__(
        self,
        title,
        product,
        unit,
        allow_decimal,
        minimum,
        initial,
        presets=(),
        price_for=None,
        price_caption=tr("so'm"),
        parent=None,
    ):
        super().__init__(title, parent, min_width=460)

        self._minimum = minimum
        self._maximum = product.quantity
        self._unit = unit
        self._price_for = price_for

        self._buffer = AmountBuffer(
            allow_decimal=allow_decimal, max_decimals=3
        )
        self._buffer.set_value(initial)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(14)

        name_label = QLabel(product.name)
        name_label.setObjectName("entryProduct")

        price_label = QLabel(
            f"{format_money(product.sell_price)} {price_caption}"
        )
        price_label.setObjectName("mutedText")

        self._field = AmountField(tr("Miqdor"), unit)
        self._field.set_active(True)

        self._hint = QLabel()
        self._hint.setObjectName("entryHint")

        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(self._field)
        layout.addWidget(self._hint)

        if presets:
            chips = QHBoxLayout()
            chips.setSpacing(10)

            for label, value in presets:
                chips.addWidget(
                    self.make_chip(
                        label, lambda _=False, v=value: self._preset(v)
                    )
                )

            layout.addLayout(chips)

        pad = NumPad(left_key="," if allow_decimal else "C")
        self.connect_numpad(pad)
        layout.addWidget(pad)

        layout.addLayout(self.build_footer())

        self.buffer_changed()

    # ---- TouchDialog ---------------------------------------------

    def active_buffer(self):
        return self._buffer

    def buffer_changed(self):
        value = self._buffer.value()
        self._field.set_text(self._buffer.display())

        valid = True
        state = "ok"

        if value < self._minimum - _EPSILON:
            message = tr("Eng kami: {0} {1}").format(format_quantity(self._minimum), self._unit)
            valid = False
        elif value > self._maximum + _EPSILON:
            message = (
                tr("Qoldiq yetarli emas: {0} {1} bor").format(format_quantity(self._maximum), self._unit)
            )
            valid = False
        elif self._price_for is not None:
            total = self._price_for(value) * value
            message = tr("Jami: {0} so'm").format(format_money(total))
        else:
            message = ""

        if not valid:
            state = "bad"

        self._hint.setText(message)
        self._hint.setProperty("state", state)
        self._hint.style().unpolish(self._hint)
        self._hint.style().polish(self._hint)
        self._field.set_state(state)
        self.ok_button.setEnabled(valid)

    def _preset(self, value):
        self._buffer.set_value(value)
        self.buffer_changed()

    def get_value(self):
        return round(self._buffer.value(), 3)
