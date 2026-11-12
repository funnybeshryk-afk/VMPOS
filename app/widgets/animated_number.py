from PySide6.QtCore import QEasingCurve, QObject, QVariantAnimation

from app.utils import motion


class AnimatedNumber(QObject):
    """Yorliqdagi sonni yangi qiymatgacha "docrutka" qiladi (~220 ms).

    formatter(value) -> yorliq matni. Animatsiya o'rtasida yangi qiymat
    kelsa — joriy ko'rsatilayotgan sondan davom etadi (sakrash yo'q).
    Oxirgi kadr HAR DOIM aniq yakuniy qiymat; animatsiya o'chiq bo'lsa
    darhol qo'yiladi."""

    def __init__(self, label, formatter, parent=None):
        super().__init__(parent or label)

        self._label = label
        self._formatter = formatter
        self._current = 0.0
        self._target = 0.0

        self._animation = QVariantAnimation(self)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._on_frame)
        self._animation.finished.connect(self._on_finished)

        self._show(0.0)

    def target(self):
        return self._target

    def current(self):
        return self._current

    def is_running(self):
        return self._animation.state() == QVariantAnimation.Running

    def set_value(self, value):
        value = float(value)
        self._target = value

        if not motion.is_enabled() or value == self._current:
            self._animation.stop()
            self._show(value)
            return

        self._animation.stop()
        self._animation.setDuration(motion.DURATION_TOTAL_MS)
        self._animation.setStartValue(self._current)
        self._animation.setEndValue(value)
        self._animation.start()

    def _on_frame(self, value):
        # Oraliq kadrlar butun songa yaxlitlanadi (tiyinlar "titramasin");
        # yakuniy qiymat esa har doim aniq (_on_finished).
        self._show(float(round(value)))

    def _on_finished(self):
        # Oxirgi kadr aniq (suzuvchi nuqta qoldig'isiz).
        self._show(self._target)

    def _show(self, value):
        self._current = value
        self._label.setText(self._formatter(value))
