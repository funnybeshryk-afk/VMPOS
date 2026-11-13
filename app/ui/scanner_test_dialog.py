import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QVBoxLayout

from app.utils.scan_burst import ScanBurstParser
from app.widgets.secondary_button import SecondaryButton


class ScannerTestDialog(QDialog):
    """Skaner nima yuborayotganini ko'rsatadi: matn, uzunlik, oxiridagi
    tugma (Enter/Tab), tezlik. Muammoni ajratish uchun: o'zingizning
    mahsulot qadog'idagi shtrix-kodni skanerlang — o'qisa, skaner joyida;
    bizning yorliq o'qilmasa — gap yorliqda."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Skaner sinovi")
        self.resize(520, 460)

        self._parser = ScanBurstParser()

        intro = QLabel(
            "Shtrix-kodni skanerlang. Skaner yuborgan narsa pastda "
            "ko'rinadi: matn, oxirgi tugma (Enter/Tab) va tezlik."
        )
        intro.setWordWrap(True)

        self.results = QListWidget()
        self.results.setFocusPolicy(Qt.NoFocus)

        self.hint = QLabel(
            "Hech narsa chiqmasa: skaner USB/klaviatura (HID) rejimida "
            "emasmi yoki ulanmaganmi, tekshiring."
        )
        self.hint.setObjectName("mutedText")
        self.hint.setWordWrap(True)

        close_button = SecondaryButton("Yopish", large=True)
        close_button.clicked.connect(self.accept)
        close_button.setFocusPolicy(Qt.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(intro)
        layout.addWidget(self.results, 1)
        layout.addWidget(self.hint)
        layout.addWidget(close_button)

        # Suffikssiz skaner uchun: tanaffusdan keyin yozuvni yopadi.
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(100)
        self._idle_timer.timeout.connect(self._on_idle)
        self._idle_timer.start()

    @staticmethod
    def _now_ms():
        return int(time.monotonic() * 1000)

    def keyPressEvent(self, event):
        now = self._now_ms()
        key = event.key()

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._show(self._parser.feed_suffix("Enter", now))
            return

        if key == Qt.Key_Tab:
            self._show(self._parser.feed_suffix("Tab", now))
            return

        text = event.text()

        if text and text.isprintable() and not text.isspace():
            for char in text:
                self._show(self._parser.feed_char(char, now))
            return

        super().keyPressEvent(event)

    def _on_idle(self):
        self._show(self._parser.flush(self._now_ms()))

    def _show(self, record):
        if record is None:
            return

        kind = "skaner tezligi" if record.looks_like_scanner else "qo'lda yozilgandek"
        suffix = record.suffix or "oxirida tugma yo'q"
        self.results.insertItem(
            0,
            f"{record.text}   |   {len(record.text)} belgi   |   {suffix}   |   "
            f"{record.duration_ms} ms ({kind})",
        )
