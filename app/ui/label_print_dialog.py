from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import QPageLayout, QPageSize, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.utils.formatters import format_money
from app.utils.label_printing import (
    LABEL_SIZE_PRESETS,
    build_label_entries,
    paint_product_label,
)
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton

_CUSTOM_SIZE_LABEL = "Boshqa..."
_PREVIEW_SCALE = 8  # 1mm = 8px, ekrandagi ko'rinish uchun


class LabelPrintDialog(QDialog):
    """Tanlangan mahsulot(lar) uchun narx yorlig'ini PDF yoki
    printerga chiqarish.

    Har bir nusxa alohida "sahifa" sifatida chiqariladi (yorliq
    printerlari odatda shunday ishlaydi — har sahifa bitta yorliq),
    shuning uchun A4 varaqqa panjara joylashtirish kabi murakkab
    tartib kerak emas.
    """

    def __init__(self, products, parent=None):
        super().__init__(parent)

        self._products = products

        self.setWindowTitle("Narx yorliqlarini chop etish")
        self.resize(560, 620)

        main_layout = QVBoxLayout(self)

        size_form = QFormLayout()

        self.size_combo = QComboBox()
        self.size_combo.addItems(list(LABEL_SIZE_PRESETS.keys()))
        self.size_combo.addItem(_CUSTOM_SIZE_LABEL)
        self.size_combo.currentTextChanged.connect(
            self._on_size_changed
        )

        self.custom_width_edit = QDoubleSpinBox()
        self.custom_width_edit.setRange(10, 200)
        self.custom_width_edit.setSuffix(" mm")
        self.custom_width_edit.setValue(40)
        self.custom_width_edit.valueChanged.connect(
            self.update_preview
        )

        self.custom_height_edit = QDoubleSpinBox()
        self.custom_height_edit.setRange(10, 200)
        self.custom_height_edit.setSuffix(" mm")
        self.custom_height_edit.setValue(30)
        self.custom_height_edit.valueChanged.connect(
            self.update_preview
        )

        custom_size_row = QHBoxLayout()
        custom_size_row.addWidget(self.custom_width_edit)
        custom_size_row.addWidget(QLabel("x"))
        custom_size_row.addWidget(self.custom_height_edit)

        size_form.addRow("Yorliq o'lchami:", self.size_combo)
        size_form.addRow("Maxsus o'lcham:", custom_size_row)

        main_layout.addLayout(size_form)

        self.items_table = DataTable()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Shtrix kod",
            "Nusxalar soni",
        ])
        self.items_table.currentCellChanged.connect(
            lambda *_: self.update_preview()
        )
        main_layout.addWidget(self.items_table)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("labelPreview")
        self.preview_label.setMinimumHeight(
            int(60 * _PREVIEW_SCALE)
        )
        main_layout.addWidget(self.preview_label)

        button_row = QHBoxLayout()

        self.export_pdf_button = SecondaryButton(
            "PDF sifatida saqlash"
        )
        self.export_pdf_button.clicked.connect(self.export_pdf)

        self.print_button = PrimaryButton("Chop etish")
        self.print_button.clicked.connect(self.print_labels)

        close_button = SecondaryButton("Yopish")
        close_button.clicked.connect(self.reject)

        button_row.addWidget(self.export_pdf_button)
        button_row.addWidget(self.print_button)
        button_row.addWidget(close_button)

        main_layout.addLayout(button_row)

        self._populate_items_table()
        self._on_size_changed(self.size_combo.currentText())

    def _populate_items_table(self):
        self.items_table.setRowCount(len(self._products))
        self._copy_inputs = {}

        for row, product in enumerate(self._products):
            name_item = QTableWidgetItem(product.name or "")
            name_item.setData(Qt.UserRole, product.id)

            self.items_table.setItem(row, 0, name_item)
            self.items_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    f"{format_money(product.sell_price)} so'm"
                ),
            )
            self.items_table.setItem(
                row,
                2,
                QTableWidgetItem(product.barcode or ""),
            )

            copies_spinbox = QSpinBox()
            copies_spinbox.setRange(1, 999)
            copies_spinbox.setValue(1)
            copies_spinbox.valueChanged.connect(
                self.update_preview
            )

            self.items_table.setCellWidget(row, 3, copies_spinbox)
            self._copy_inputs[product.id] = copies_spinbox

        if self._products:
            self.items_table.selectRow(0)

    def _on_size_changed(self, text):
        is_custom = text == _CUSTOM_SIZE_LABEL

        self.custom_width_edit.setEnabled(is_custom)
        self.custom_height_edit.setEnabled(is_custom)

        if not is_custom:
            width_mm, height_mm = LABEL_SIZE_PRESETS[text]
            self.custom_width_edit.blockSignals(True)
            self.custom_height_edit.blockSignals(True)
            self.custom_width_edit.setValue(width_mm)
            self.custom_height_edit.setValue(height_mm)
            self.custom_width_edit.blockSignals(False)
            self.custom_height_edit.blockSignals(False)

        self.update_preview()

    def get_label_size_mm(self):
        return (
            self.custom_width_edit.value(),
            self.custom_height_edit.value(),
        )

    def _selected_preview_product(self):
        current_row = self.items_table.currentRow()

        if current_row < 0 or current_row >= len(self._products):
            return self._products[0] if self._products else None

        return self._products[current_row]

    def update_preview(self):
        product = self._selected_preview_product()

        if product is None:
            self.preview_label.clear()
            return

        width_mm, height_mm = self.get_label_size_mm()

        pixmap_width = max(1, int(width_mm * _PREVIEW_SCALE))
        pixmap_height = max(1, int(height_mm * _PREVIEW_SCALE))

        pixmap = QPixmap(pixmap_width, pixmap_height)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        paint_product_label(
            painter,
            QRectF(0, 0, pixmap_width, pixmap_height),
            product,
        )
        painter.end()

        self.preview_label.setPixmap(pixmap)

    def _collect_entries(self):
        products_with_copies = [
            (product, self._copy_inputs[product.id].value())
            for product in self._products
        ]

        return build_label_entries(products_with_copies)

    def _render_to_printer(self, printer, entries):
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for index, product in enumerate(entries):
            if index > 0:
                printer.newPage()

            rect = QRectF(printer.pageRect(QPrinter.DevicePixel))
            paint_product_label(painter, rect, product)

        painter.end()

    def _build_printer(self):
        width_mm, height_mm = self.get_label_size_mm()

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(
            QPageSize(
                QSizeF(width_mm, height_mm), QPageSize.Millimeter
            )
        )
        printer.setPageMargins(
            QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter
        )
        printer.setFullPage(True)

        return printer

    def print_labels(self):
        entries = self._collect_entries()

        if not entries:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Chop etish uchun mahsulot topilmadi.",
            )
            return

        printer = self._build_printer()

        print_dialog = QPrintDialog(printer, self)

        if not print_dialog.exec():
            return

        self._render_to_printer(printer, entries)

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"{len(entries)} ta yorliq chop etildi.",
        )

    def export_pdf(self):
        entries = self._collect_entries()

        if not entries:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Saqlash uchun mahsulot topilmadi.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF sifatida saqlash",
            "narx_yorliqlari.pdf",
            "PDF fayllar (*.pdf)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        printer = self._build_printer()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)

        self._render_to_printer(printer, entries)

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"Saqlandi: {file_path}",
        )
