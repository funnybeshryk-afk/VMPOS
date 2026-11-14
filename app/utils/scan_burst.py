"""Skaner yuborgan "portlash"ni (tez belgilar + oxirida Enter/Tab) tahlil
qilish — "Skaner sinovi" uchun. UI'dan mustaqil, sinaladi.

Haqiqiy skaner 13 belgini ~10-30 ms ichida yuboradi (belgilar orasida
bir necha ms); odam esa 100+ ms. Shu farq bo'yicha "skaner tezligi"
aniqlanadi.
"""

from dataclasses import dataclass

IDLE_MS = 300          # shuncha tinchlikdan keyin portlash tugagan hisoblanadi
SCANNER_MAX_MS_PER_CHAR = 40


@dataclass
class ScanRecord:
    text: str
    suffix: str            # "Enter" | "Tab" | "" (oxirida belgi yo'q)
    duration_ms: int
    ms_per_char: float

    @property
    def looks_like_scanner(self):
        return len(self.text) >= 4 and self.ms_per_char <= SCANNER_MAX_MS_PER_CHAR


class ScanBurstParser:
    def __init__(self):
        self._chars = []
        self._first_ms = 0
        self._last_ms = 0

    def feed_char(self, char, now_ms):
        """Oddiy belgi. Oldingi portlash tugagan bo'lsa (uzoq tanaffus) —
        o'sha yozuvni qaytaradi."""

        finished = self.flush(now_ms)

        if not self._chars:
            self._first_ms = now_ms

        self._chars.append(char)
        self._last_ms = now_ms

        return finished

    def feed_suffix(self, name, now_ms):
        """Enter/Tab keldi — portlash tugadi (belgi bo'lmasa None)."""

        finished = self.flush(now_ms)

        if finished is not None:
            return finished

        return self._finish(name)

    def flush(self, now_ms):
        """Uzoq tinchlikdan keyin tugatilmagan portlashni yopadi."""

        if self._chars and now_ms - self._last_ms > IDLE_MS:
            return self._finish("")

        return None

    def _finish(self, suffix):
        if not self._chars:
            return None

        text = "".join(self._chars)
        duration = self._last_ms - self._first_ms
        record = ScanRecord(
            text=text,
            suffix=suffix,
            duration_ms=duration,
            ms_per_char=duration / max(1, len(text) - 1) if len(text) > 1 else 0.0,
        )
        self._chars = []

        return record
