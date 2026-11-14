import time
from datetime import datetime

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

from app.services.receipt_service import ReceiptService
from app.utils import receipt_render
from app.utils.scan_burst import ScanBurstParser
from app.widgets.badge import StatusBadge, set_badge_variant

_HOTKEYS = [
    ("F2", "Qidiruv"),
    ("F5", "Bekor qilish"),
    ("F4", "To'lov"),
]

_PRINTER_REFRESH_MS = 10_000


def printer_state(saved_name, available, default_name):
    """Chek printeri holati: (matn, variant). Sof mantiq — sinash oson.

    saved_name "" — "Tizim standarti". Printer topilmasa chek baribir
    PDF sifatida saqlanadi, shuning uchun bu "xato" emas, "PDF".
    """

    if saved_name:
        if saved_name in available:
            return "Tayyor", "success"

        return "Topilmadi", "danger"

    if default_name and default_name in available:
        return "Tayyor", "success"

    return "PDF", "neutral"


class ScanActivityMonitor(QObject):
    """USB-skaner klaviatura bo'lib yozadi, shuning uchun uni "ulangan"
    deb bilib bo'lmaydi — faqat haqiqatan skanerlanganini ko'ramiz:
    tez belgilar oqimi (odam bunchalik tez yozmaydi). Dastur ichidagi
    barcha tugmalarni kuzatadi, hech narsani to'smaydi.
    """

    def __init__(self, on_scan, clock=None):
        super().__init__()

        self._on_scan = on_scan
        self._parser = ScanBurstParser()
        self._clock = clock or (lambda: int(time.monotonic() * 1000))

    def handle_key(self, text, key_name=""):
        """text — bosilgan belgi, key_name — "Enter"/"Tab" yoki ""."""

        now = self._clock()

        if key_name:
            record = self._parser.feed_suffix(key_name, now)
        elif text and text.isprintable() and not text.isspace():
            record = self._parser.feed_char(text, now)
        else:
            return

        if record is not None and record.looks_like_scanner:
            self._on_scan(record)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and not event.isAutoRepeat():
            key_name = {
                Qt.Key_Return: "Enter",
                Qt.Key_Enter: "Enter",
                Qt.Key_Tab: "Tab",
            }.get(event.key(), "")
            self.handle_key(event.text(), key_name)

        return False


class AppStatusBar(QWidget):
    """Pastki qatordagi tezkor klavishlar va uskunalar holati.

    Printer — haqiqiy tekshiruv (sozlamadagi chek printeri tizimda bormi,
    har 10 soniyada yangilanadi). Skaner — oxirgi haqiqiy skanerlash
    vaqti. Tarozi qo'llab-quvvatlanmagani uchun ko'rsatilmaydi.
    """

    def __init__(self, install_scan_monitor=True):
        super().__init__()

        self.setObjectName("statusBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(20)

        hotkeys_text = "    ".join(
            f"{key} — {label}" for key, label in _HOTKEYS
        )
        hotkeys_label = QLabel(hotkeys_text)
        hotkeys_label.setObjectName("statusBarHint")

        layout.addWidget(hotkeys_label)
        layout.addStretch()

        self.scanner_badge = StatusBadge("Kutilmoqda", "neutral")
        self.printer_badge = StatusBadge("PDF", "neutral")

        layout.addWidget(self._indicator("Skaner", self.scanner_badge))
        layout.addWidget(self._indicator("Printer", self.printer_badge))

        self.refresh_printer()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_printer)
        self._timer.start(_PRINTER_REFRESH_MS)

        self._monitor = None

        if install_scan_monitor:
            self._monitor = ScanActivityMonitor(self.note_scan)
            QApplication.instance().installEventFilter(self._monitor)

    def note_scan(self, record):
        set_badge_variant(
            self.scanner_badge,
            f"Skan {datetime.now():%H:%M}",
            "success",
        )
        self.scanner_badge.setToolTip(
            f"Oxirgi shtrix-kod: {record.text} "
            f"({record.ms_per_char:.0f} ms/belgi)"
        )

    def refresh_printer(self):
        try:
            saved = ReceiptService.get_settings()["printer"]
            text, variant = printer_state(
                saved,
                receipt_render.available_printers(),
                receipt_render.default_printer_name(),
            )
        except Exception:
            text, variant = "Noma'lum", "neutral"

        set_badge_variant(self.printer_badge, text, variant)

    @staticmethod
    def _indicator(device_name, badge):
        container = QWidget()

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)

        name_label = QLabel(device_name)
        name_label.setObjectName("statusBarHint")

        container_layout.addWidget(name_label)
        container_layout.addWidget(badge)

        return container
