from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.icons import load_checkable_icon

_ICON_SIZE = 24
_ITEM_SIZE = QSize(76, 62)
_ICON_COLOR_UNCHECKED = "#a8a29e"
_ICON_COLOR_CHECKED = "#ffffff"


class SidebarMenu(QWidget):
    """Chap "rels" menyusi: ikonka tepada, qisqa yozuv pastda.

    Barmoq uchun katta zonalar (76x62), yagona tanlangan band —
    izumrud ramkali. Guruhlar (Asosiy / Aloqalar / Boshqaruv) endi
    sarlavhasiz, ingichka chiziq bilan ajratiladi — 96 px kenglikka
    sarlavha sig'maydi. To'liq nom — tooltip'da.

    Rolga qarab ko'rinmaydigan bandlar va butunlay bo'sh guruhlar
    avvalgidek o'tkazib yuboriladi.
    """

    itemSelected = Signal(str)

    def __init__(self):
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignHCenter)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._buttons_by_key = {}

    def set_groups(self, groups):
        """groups: [(sarlavha, [(key, label, icon_name[, tooltip]), ...]), ...].

        Sarlavha endi ko'rsatilmaydi (API eski chaqiruvlar bilan mos
        qolishi uchun saqlangan)."""

        while self._layout.count():
            layout_item = self._layout.takeAt(0)
            widget = layout_item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        for button in list(self._button_group.buttons()):
            self._button_group.removeButton(button)

        self._buttons_by_key = {}

        first_group = True

        for _group_title, entries in groups:
            if not entries:
                continue

            if not first_group:
                self._layout.addWidget(
                    self._make_separator(), 0, Qt.AlignHCenter
                )

            first_group = False

            for entry in entries:
                key, label, icon_name = entry[:3]
                tooltip = entry[3] if len(entry) > 3 else label

                self._layout.addWidget(
                    self._make_button(key, label, icon_name, tooltip),
                    0,
                    Qt.AlignHCenter,
                )

        self._layout.addStretch()

    def _make_separator(self):
        line = QFrame()
        line.setObjectName("railSeparator")
        line.setFixedSize(40, 1)

        return line

    def _make_button(self, key, label, icon_name, tooltip):
        button = QToolButton()
        button.setObjectName("railItem")
        button.setText(label)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setAutoRaise(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setFixedSize(_ITEM_SIZE)
        button.setIcon(
            load_checkable_icon(
                icon_name,
                _ICON_COLOR_UNCHECKED,
                _ICON_COLOR_CHECKED,
                _ICON_SIZE,
            )
        )
        button.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))

        button.toggled.connect(
            lambda checked, k=key: (
                self.itemSelected.emit(k) if checked else None
            )
        )

        self._button_group.addButton(button)
        self._buttons_by_key[key] = button

        return button

    def select(self, key):
        button = self._buttons_by_key.get(key)

        if button is not None:
            button.setChecked(True)

    def has_key(self, key):
        return key in self._buttons_by_key
