from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton

from app.utils.amount_buffer import apply_key_event
from app.widgets.secondary_button import SecondaryButton
from app.widgets.success_button import SuccessButton


class TouchDialog(QDialog):
    """Sensorli kiritish dialogi uchun umumiy asos.

    * raqamli blok (NumPad) bosilishlari faol buferga uzatiladi;
    * jismoniy klaviatura (raqamlar, vergul, Backspace, Delete) HAM
      xuddi shunday ishlaydi — kassa klaviaturali bo'lsa, hech narsa
      yo'qolmaydi;
    * Enter — tasdiqlash tugmasi (u faol bo'lsa), Esc — bekor qilish
      (QDialog'ning o'zi).

    Voris active_buffer() va buffer_changed() ni belgilaydi.
    """

    def __init__(self, title, parent=None, min_width=480):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)

        self.ok_button = None

    # ---- vorislar uchun ------------------------------------------

    def active_buffer(self):
        raise NotImplementedError

    def buffer_changed(self):
        raise NotImplementedError

    # ---- umumiy qismlar ------------------------------------------

    def build_footer(self, ok_text="Tasdiqlash"):
        cancel = SecondaryButton("Bekor qilish", large=True)
        cancel.setObjectName("dialogCancel")
        cancel.setFocusPolicy(Qt.NoFocus)
        cancel.clicked.connect(self.reject)

        self.ok_button = SuccessButton(ok_text, large=True)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(cancel, 1)
        row.addWidget(self.ok_button, 2)

        return row

    def make_chip(self, text, handler):
        chip = QPushButton(text)
        chip.setObjectName("padChip")
        chip.setFocusPolicy(Qt.NoFocus)
        chip.setCursor(Qt.PointingHandCursor)
        chip.clicked.connect(handler)

        return chip

    def connect_numpad(self, pad):
        pad.digitPressed.connect(lambda digit: self._edit("digit", digit))
        pad.zerosPressed.connect(lambda: self._edit("zeros"))
        pad.decimalPressed.connect(lambda: self._edit("decimal"))
        pad.clearPressed.connect(lambda: self._edit("clear"))
        pad.backspacePressed.connect(lambda: self._edit("backspace"))

    def _edit(self, action, value=None):
        buffer = self.active_buffer()

        if buffer is None:
            return

        if action == "digit":
            buffer.press_digit(value)
        elif action == "zeros":
            buffer.press_zeros()
        elif action == "decimal":
            buffer.press_decimal()
        elif action == "clear":
            buffer.clear()
        elif action == "backspace":
            buffer.backspace()

        self.buffer_changed()

    def keyPressEvent(self, event):
        buffer = self.active_buffer()

        if buffer is not None and apply_key_event(buffer, event):
            self.buffer_changed()
            return

        super().keyPressEvent(event)
