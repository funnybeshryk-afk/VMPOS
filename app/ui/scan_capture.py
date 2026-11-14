from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
)

_TEXT_WIDGETS = (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox)


class ScanCapture(QObject):
    """Shtrix-kod skaneri klaviatura sifatida yozadi: raqamlar (+ Enter).
    Fokus qidiruv maydonida bo'lmasa (tugma, ro'yxat...), bu raqamlar
    yo'qolib ketardi. Bu filtr Sotuv ochiq paytida bosilgan oddiy
    belgi/raqamni qidiruv maydoniga yo'naltiradi va fokusni shu yerga
    qaytaradi.

    Aralashmaydi: modal dialog ochiq bo'lsa, boshqa oyna faol bo'lsa,
    fokus matn maydonida bo'lsa, Ctrl/Alt bosilgan bo'lsa yoki tugma
    matnsiz (F2, Enter, Tab...) bo'lsa.
    """

    def __init__(self, page, search_edit):
        super().__init__(page)

        self._page = page
        self._search_edit = search_edit

        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return False

        if not self._should_capture(event):
            return False

        self._search_edit.setFocus(Qt.OtherFocusReason)
        # Yangi skanerlash eski (qolib ketgan) matnni almashtirsin.
        self._search_edit.selectAll()

        forwarded = QKeyEvent(
            event.type(), event.key(), event.modifiers(), event.text()
        )
        QApplication.sendEvent(self._search_edit, forwarded)

        return True

    def _should_capture(self, event):
        app = QApplication.instance()

        if not self._page.isVisible():
            return False

        if app.activeModalWidget() is not None:
            return False

        if app.activeWindow() is not self._page.window():
            return False

        focus = app.focusWidget()

        if focus is self._search_edit or isinstance(focus, _TEXT_WIDGETS):
            return False

        if isinstance(focus, QComboBox) and focus.isEditable():
            return False

        if event.modifiers() & (
            Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
        ):
            return False

        text = event.text()

        return bool(text) and text.isprintable() and not text.isspace()
