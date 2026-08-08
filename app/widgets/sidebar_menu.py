from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.icons import load_checkable_icon

_ICON_SIZE = 18
_ICON_COLOR_UNCHECKED = "#57534e"
_ICON_COLOR_CHECKED = "#ffffff"


class SidebarMenu(QWidget):
    """Guruhlangan, ikonkali, rolga qarab moslashuvchi sidebar menyusi.

    QListWidget o'rniga ataylab QPushButton + QButtonGroup bilan
    qurilgan (CategoryBar'dagi kabi naqsh) — chunki QListWidget'da
    band ichida ikonka + guruh sarlavhalarini (ba'zi bandlar
    tanlab bo'lmaydigan, boshqacha uslubdagi qatorlar) tabiiy
    qo'llab-quvvatlash yo'q. Bo'sh guruh (rol bo'yicha bironta ham
    bandi ko'rinmasa) sarlavhasiz butunlay o'tkazib yuboriladi.
    """

    itemSelected = Signal(str)

    def __init__(self):
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(2)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._buttons_by_key = {}

    def set_groups(self, groups):
        """groups: [(sarlavha, [(key, label, icon_name), ...]), ...]."""

        while self._layout.count():
            layout_item = self._layout.takeAt(0)
            widget = layout_item.widget()

            if widget is not None:
                # deleteLater() faqat keyingi event loop navbatida
                # o'chiradi — o'sha payгacha vidjet hali ота-onaga
                # bog'langan va eski joyida chizilaveradi. setParent
                # (None) uni darhol ekrandan yo'qotadi, deleteLater()
                # esa xotirani xavfsiz tozalaydi.
                widget.setParent(None)
                widget.deleteLater()

        for button in list(self._button_group.buttons()):
            self._button_group.removeButton(button)

        self._buttons_by_key = {}

        for group_title, entries in groups:
            if not entries:
                continue

            self._layout.addWidget(
                self._make_group_header(group_title)
            )

            for key, label, icon_name in entries:
                self._layout.addWidget(
                    self._make_button(key, label, icon_name)
                )

        self._layout.addStretch()

    def _make_group_header(self, title):
        header = QWidget()
        header.setObjectName("sidebarGroupHeader")

        layout = QHBoxLayout(header)
        # Yuqori 16px — oldingi menyu bandidan ajratish uchun; chap/
        # o'ng 8px — menyu bandlari bilan bir xil chetga tekislash
        # uchun (konteynerning o'zida 8px tashqi hoshiya bor).
        layout.setContentsMargins(8, 16, 8, 4)
        layout.setSpacing(8)

        title_label = QLabel(title.upper())
        title_label.setObjectName("sidebarGroupTitle")

        line = QFrame()
        line.setObjectName("sidebarGroupLine")
        line.setFixedHeight(1)

        layout.addWidget(title_label)
        layout.addWidget(line, 1)

        return header

    def _make_button(self, key, label, icon_name):
        button = QPushButton(label)
        button.setObjectName("sidebarMenuItem")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(
            load_checkable_icon(
                icon_name,
                _ICON_COLOR_UNCHECKED,
                _ICON_COLOR_CHECKED,
                _ICON_SIZE,
            )
        )
        button.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))

        # clicked emasa toggled: select() orqali dasturiy tanlash ham
        # (masalan sahifa ochilganda odatiy bandni belgilash) xuddi
        # foydalanuvchi bosgandagidek ishlashi kerak — clicked faqat
        # haqiqiy bosishda ishga tushadi, toggled esa har ikkalasida.
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
