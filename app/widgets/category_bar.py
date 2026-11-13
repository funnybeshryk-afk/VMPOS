from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QScroller,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
)

from app.utils.category_icons import icon_for_category
from app.utils.icons import load_checkable_icon

_ALL_LABEL = "Barchasi"
_ALL_ICON = "grid"
_BAR_HEIGHT = 62

_ICON_SIZE = 16
_ICON_COLOR_UNCHECKED = "#44403c"
_ICON_COLOR_CHECKED = "#ffffff"


def _icon_for_tile(category):
    if category is None:
        return _ALL_ICON

    return icon_for_category(category)


class CategoryBar(QWidget):
    """Плиточная панель категорий для быстрого тапа на сенсорном экране.

    Одна строка с горизонтальной прокруткой — на кассе редко бывает
    больше десятка категорий, прокрутка пальцем по горизонтали здесь
    привычнее вертикальной сетки (так делают Square, Toast и другие
    POS). Категории берутся из реальных данных (Product.category),
    а не задаются заранее — set_categories() перестраивает плитки
    под то, что реально есть на складе.
    """

    categorySelected = Signal(object)

    def __init__(self):
        super().__init__()

        # QScrollArea'ning o'zi Expanding vertikal siyosat bilan
        # tug'iladi (setFixedHeight faqat min/max'ni cheklaydi, lekin
        # siyosatni o'zgartirmaydi) — shu sabab tashqi QVBoxLayout
        # (Sotuv sahifasida) ortiqcha bo'sh joyni shu vidjetga ham
        # bera boshlaydi va panel ichida katta bo'sh joy paydo
        # bo'ladi. CategoryBar'ning o'zini ham qat'iy balandlikka
        # qulflab, bu muammoning oldini olamiz.
        self.setFixedHeight(_BAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("categoryScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFixedHeight(_BAR_HEIGHT)
        # Skroll-bar yo'q: sensorli ekranda barmoq bilan suriladi
        # (TouchGesture), sichqonchada — g'ildirak bilan (wheelEvent).
        # Ko'rinib turgan skroll-bar plitkalarni kesib, qator
        # balandligini "yeb" qo'yardi.
        self._scroll_area.setFocusPolicy(Qt.NoFocus)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setAutoFillBackground(False)
        self._scroll_area.viewport().setAutoFillBackground(False)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        QScroller.grabGesture(
            self._scroll_area.viewport(), QScroller.TouchGesture
        )
        self._scroll_area.wheelEvent = self._scroll_horizontally
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        # QScrollArea.viewport() — отдельный внутренний виджет между
        # рамкой и содержимым; у него своя закраска фона, и QSS не
        # достаёт до него через комбинаторы-потомки надёжно (структура
        # приватная и может отличаться от предположений). Называем
        # явно и красим все три слоя отдельно — вместо угадывания.
        self._scroll_area.viewport().setObjectName(
            "categoryScrollViewport"
        )

        self._content = QWidget()
        self._content.setObjectName("categoryBarContent")

        self._tiles_layout = QHBoxLayout(self._content)
        self._tiles_layout.setContentsMargins(2, 6, 2, 6)
        self._tiles_layout.setSpacing(8)

        self._scroll_area.setWidget(self._content)
        layout.addWidget(self._scroll_area)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self.set_categories([])

    def _scroll_horizontally(self, event):
        """G'ildirak — gorizontal skroll (vertikal skroll bu yerda yo'q)."""

        bar = self._scroll_area.horizontalScrollBar()
        delta = event.angleDelta().y() or event.angleDelta().x()

        bar.setValue(bar.value() - delta)
        event.accept()

    def set_categories(self, categories):
        """Перестраивает плитки. "Barchasi" всегда первая и активная."""

        while self._tiles_layout.count():
            item = self._tiles_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                self._button_group.removeButton(widget)
                # deleteLater() o'chirishni keyingi sikl iteratsiyasiga
                # qoldiradi — shu paytgacha eski plitka (eski
                # geometriya bilan) ko'rinib turardi.
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        all_tile = self._make_tile(_ALL_LABEL, None)
        self._tiles_layout.addWidget(all_tile)
        all_tile.setChecked(True)

        for category in categories:
            self._tiles_layout.addWidget(
                self._make_tile(category, category)
            )

        self._tiles_layout.addStretch()

    def _make_tile(self, label, value):
        tile = QPushButton(label)
        tile.setObjectName("categoryTile")
        tile.setCheckable(True)
        tile.setCursor(Qt.PointingHandCursor)
        tile.setFocusPolicy(Qt.NoFocus)
        tile.setIcon(
            load_checkable_icon(
                _icon_for_tile(value),
                _ICON_COLOR_UNCHECKED,
                _ICON_COLOR_CHECKED,
                _ICON_SIZE,
            )
        )
        tile.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        tile.clicked.connect(
            lambda: self.categorySelected.emit(value)
        )

        self._button_group.addButton(tile)

        return tile
