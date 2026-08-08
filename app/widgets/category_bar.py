from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
)

_ALL_LABEL = "Barchasi"


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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("categoryScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFixedHeight(56)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
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

    def set_categories(self, categories):
        """Перестраивает плитки. "Barchasi" всегда первая и активная."""

        while self._tiles_layout.count():
            item = self._tiles_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                self._button_group.removeButton(widget)
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
        tile.clicked.connect(
            lambda: self.categorySelected.emit(value)
        )

        self._button_group.addButton(tile)

        return tile
