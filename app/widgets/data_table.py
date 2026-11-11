from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
)

_HOVER_COLOR = QColor("#faf8f4")


class _RowHoverDelegate(QStyledItemDelegate):
    """Красит фон ячейки в цвет наведения, если наведена вся её строка.

    Обычный QSS ":hover" в Qt подсвечивает только ту ячейку, что прямо
    под курсором, а не всю строку. Чтобы получить "подсветка строки
    целиком", нужен делегат отрисовки — QSS одних селекторов недостаточно.
    """

    def __init__(self, table):
        super().__init__(table)
        self._table = table

    def paint(self, painter, option, index):
        is_hovered = index.row() == self._table.hovered_row
        is_selected = bool(option.state & QStyle.State_Selected)

        if is_hovered and not is_selected:
            painter.save()
            painter.fillRect(option.rect, _HOVER_COLOR)
            painter.restore()

        super().paint(painter, option, index)


class DataTable(QTableWidget):
    """Таблица с единым для всего приложения поведением.

    Раньше каждая страница вручную повторяла один и тот же набор
    настроек (без редактирования, выбор целой строкой, без сетки,
    зебра, растянутые колонки). Теперь это в одном месте — и заодно
    все таблицы приложения ведут себя одинаково: строка целиком
    выделяется и подсвечивается при наведении, а не отдельная ячейка.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hovered_row = -1

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(36)
        self.verticalHeader().setMinimumSectionSize(36)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.horizontalHeader().setStretchLastSection(True)

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setItemDelegate(_RowHoverDelegate(self))
        self.entered.connect(self._set_hovered_row)

    def _set_hovered_row(self, index):
        row = index.row()

        if row == self.hovered_row:
            return

        previous_row = self.hovered_row
        self.hovered_row = row

        self._repaint_row(previous_row)
        self._repaint_row(row)

    def leaveEvent(self, event):
        self._repaint_row(self.hovered_row)
        self.hovered_row = -1

        super().leaveEvent(event)

    def pin_column_width(self, column):
        """Колонка перестаёт сжиматься наравне с остальными.

        По умолчанию все колонки в Stretch-режиме делят ширину
        поровну — на узком окне колонка с бейджем статуса может
        стать уже, чем сам бейдж, и QLabel просто обрежет текст
        (без переноса и без многоточия). ResizeToContents вместо
        этого спрашивает у виджета ячейки его реальный размер и
        подгоняет колонку под него — бейджу всегда хватает места.
        """

        self.horizontalHeader().setSectionResizeMode(
            column, QHeaderView.ResizeToContents
        )

    def _repaint_row(self, row):
        if row < 0:
            return

        for column in range(self.columnCount()):
            index = self.model().index(row, column)
            self.viewport().update(self.visualRect(index))
