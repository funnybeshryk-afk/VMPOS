"""Sensorli kiritish uchun raqamli bufer (miqdor, og'irlik, to'lov summasi).

Kassirga "maydonni bosib, klaviaturada yozish" o'rniga katta tugmalar
beriladi; bu klass tugmalar (va jismoniy klaviatura) bosilishini
qanday qilib songa aylantirishini belgilaydi. UI'dan mustaqil —
osongina sinaladi.

Qoidalar:
  * "yangi" holat (dialog ochilganda yoki tayyor summa tanlanganda):
    birinchi raqam eski qiymatni ALMASHTIRADI — kassir tayyor summani
    o'chirib o'tirmaydi;
  * kasr belgisi — vergul (format_money/parse_number bilan bir xil);
  * ortiqcha nol ("007") yig'ilmaydi, uzunlik cheklangan.
"""

from decimal import Decimal


class AmountBuffer:
    def __init__(self, allow_decimal=False, max_decimals=3, max_int_digits=12):
        self.allow_decimal = allow_decimal
        self.max_decimals = max_decimals
        self.max_int_digits = max_int_digits

        self._raw = ""
        self._fresh = False

    # ---- holat ----------------------------------------------------

    def set_value(self, value):
        """Tayyor qiymat qo'yadi; keyingi raqam uni almashtiradi."""

        number = Decimal(str(value or 0)).normalize()
        text = f"{number:f}".replace(".", ",")

        if not self.allow_decimal:
            text = text.split(",")[0]

        self._raw = "" if text in ("0", "") else text
        self._fresh = True

    def clear(self):
        self._raw = ""
        self._fresh = False

    def value(self):
        raw = self._raw.replace(",", ".")

        if raw in ("", "."):
            return 0.0

        return float(raw.rstrip("."))

    def raw(self):
        return self._raw

    # ---- tugmalar -------------------------------------------------

    def _start_typing(self):
        if self._fresh:
            self._raw = ""
            self._fresh = False

    def press_digit(self, digit):
        if digit not in "0123456789" or len(digit) != 1:
            return

        self._start_typing()

        integer_part, _sep, decimal_part = self._raw.partition(",")
        has_decimal = "," in self._raw

        if has_decimal:
            if len(decimal_part) >= self.max_decimals:
                return
        else:
            if len(integer_part.lstrip("0")) >= self.max_int_digits:
                return

            if integer_part == "0":
                # "0" + raqam: yetakchi nolni almashtiramiz ("05" -> "5").
                self._raw = digit if digit != "0" else "0"
                return

        self._raw += digit

    def press_zeros(self, count=3):
        # "000" — katta summalarni tez kiritish uchun; bo'sh/0 ustiga
        # nol yig'ilmaydi.
        # Yangi holatda ("tayyor summa") "000" hech narsa qilmaydi, aks
        # holda u summani o'chirib yuborar edi.
        if self._fresh:
            return

        for _ in range(count):
            if self._raw in ("", "0"):
                return

            self.press_digit("0")

    def press_decimal(self):
        if not self.allow_decimal:
            return

        self._start_typing()

        if "," in self._raw:
            return

        self._raw = (self._raw or "0") + ","

    def backspace(self):
        # Tayyor summa ustida Backspace — uni oxiridan qisqartiradi
        # (almashtirmaydi): kassir "100 000" ni "10 000" ga tuzatishi mumkin.
        self._fresh = False
        self._raw = self._raw[:-1]

    def is_fresh(self):
        return self._fresh

    def add(self, amount):
        """Tezkor "+50 000" (qog'oz pul) tugmalari.

        Tayyor (hali tegilmagan) summa ustiga bosilsa — uni ALMASHTIRADI
        (kassir 84 000 ni o'chirib o'tirmaydi: mijoz 100 000 berdi), keyingi
        bosishlar esa yig'iladi (100 000 + 50 000)."""

        base = 0 if self._fresh else self.value()
        total = base + amount

        self._raw = f"{total:.0f}" if float(total).is_integer() else f"{total}".replace(".", ",")
        self._fresh = False

    # ---- ko'rinish ------------------------------------------------

    def display(self, grouped=True):
        """Ekranda ko'rinadigan matn: "1 250 000" yoki "2,5"."""

        if self._raw == "":
            return "0"

        integer_part, sep, decimal_part = self._raw.partition(",")

        if grouped and integer_part:
            integer_part = f"{int(integer_part):,}".replace(",", " ")

        return integer_part + sep + decimal_part


def apply_key_event(buffer, event):
    """Jismoniy klaviatura: raqamlar, vergul/nuqta, Backspace.
    True qaytarsa — tugma ishlatildi (voqea qayta ishlanmasin)."""

    from PySide6.QtCore import Qt

    key = event.key()

    if Qt.Key_0 <= key <= Qt.Key_9:
        buffer.press_digit(chr(key))
        return True

    if key in (Qt.Key_Comma, Qt.Key_Period):
        buffer.press_decimal()
        return True

    if key == Qt.Key_Backspace:
        buffer.backspace()
        return True

    if key == Qt.Key_Delete:
        buffer.clear()
        return True

    return False
