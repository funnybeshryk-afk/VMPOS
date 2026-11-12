from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NumPad(QWidget):
    """Katta raqamli tugmalar (3x4) — sensorli ekranda kiritish uchun.

    Faqat signal chiqaradi, maydonni o'zi o'zgartirmaydi: bufer va
    tekshiruv dialogda (AmountBuffer). Tugmalar fokusni OLMAYDI
    (NoFocus) — jismoniy klaviatura va skaner kiritishi buzilmaydi.

    Chap pastki tugma (left_key): "000" (pul), "," (kasr, og'irlik) yoki
    "C" (tozalash — butun miqdor).
    """

    digitPressed = Signal(str)
    zerosPressed = Signal()
    decimalPressed = Signal()
    clearPressed = Signal()
    backspacePressed = Signal()

    def __init__(self, left_key="000"):
        super().__init__()

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)

        for index in range(9):
            digit = str(index + 1)
            grid.addWidget(
                self._key(digit, lambda _=False, d=digit: self.digitPressed.emit(d)),
                index // 3,
                index % 3,
            )

        if left_key == ",":
            left = self._key(",", lambda: self.decimalPressed.emit())
        elif left_key == "C":
            left = self._key("C", lambda: self.clearPressed.emit())
        else:
            left = self._key("000", lambda: self.zerosPressed.emit())

        grid.addWidget(left, 3, 0)
        grid.addWidget(
            self._key("0", lambda: self.digitPressed.emit("0")), 3, 1
        )

        backspace = self._key("⌫", lambda: self.backspacePressed.emit())
        backspace.setAutoRepeat(True)
        backspace.setAutoRepeatDelay(400)
        backspace.setAutoRepeatInterval(90)
        grid.addWidget(backspace, 3, 2)

    def _key(self, text, handler):
        button = QPushButton(text)
        button.setObjectName("padKey")
        button.setFocusPolicy(Qt.NoFocus)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(handler)

        return button


class AmountField(QFrame):
    """Katta ko'rsatkich: sarlavha + yirik qiymat (+ birlik). Bosish
    mumkin — "shuni tahrirlayman" (clicked); faol maydon izumrud
    ramka bilan ajraladi. Aralash to'lovda ikkita shunday maydon bor."""

    clicked = Signal()

    def __init__(self, caption, unit=""):
        super().__init__()

        self.setObjectName("amountField")
        self.setProperty("active", "false")
        self.setProperty("state", "ok")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(104)

        self._caption = QLabel(caption)
        self._caption.setObjectName("amountCaption")

        self._value = QLabel("0")
        self._value.setObjectName("amountValue")

        self._unit = QLabel(unit)
        self._unit.setObjectName("amountUnit")

        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        value_row.addWidget(self._value)
        value_row.addWidget(self._unit, 0, Qt.AlignBottom)
        value_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(0)
        layout.addWidget(self._caption)
        layout.addLayout(value_row)

    def set_text(self, text):
        self._value.setText(text)

    def text(self):
        return self._value.text()

    def set_active(self, active):
        self._set_property("active", "true" if active else "false")

    def set_state(self, state):
        """"ok" yoki "bad" (qizil ramka — noto'g'ri qiymat)."""

        self._set_property("state", state)

    def _set_property(self, name, value):
        self.setProperty(name, value)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
