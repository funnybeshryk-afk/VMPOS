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
    SHEET_HEIGHT_MM,
    SHEET_WIDTH_MM,
    build_label_entries,
    compute_grid_layout,
    paginate_entries,
    paint_label_sheet,
)
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton

_CUSTOM_SIZE_LABEL = "Boshqa..."
_COPIES_COLUMN = 3

# Preview — A4 varaqning kichraytirilgan maketi (haqiqiy nisbatda),
# yorliq o'lchamidan qat'iy nazar doim shu piksel o'lchamda —
# faqat ichidagi panjara (necha ustun/qator) o'zgaradi.
_SHEET_PREVIEW_WIDTH = 260
_SHEET_PREVIEW_HEIGHT = int(
    _SHEET_PREVIEW_WIDTH * SHEET_HEIGHT_MM / SHEET_WIDTH_MM
)


class LabelPrintDialog(QDialog):
    """Tanlangan mahsulot(lar) uchun narx yorlig'ini PDF yoki
    printerga chiqarish.

    Yorliqlar A4 varaqqa panjara (grid) tartibida joylashtiriladi —
    har varaqqa yorliq o'lchamiga qarab bir nechtasi sig'adi (masalan
    40x30mm'da ~36 dona). Preview xuddi shu tartibni (haqiqiy
    nisbatda, kichraytirilgan) ko'rsatadi — nima chop etilsa, preview
    aynan shuni aks ettiradi.
    """

    def __init__(self, products, parent=None):
        super().__init__(parent)

        self._products = products

        self.setWindowTitle("Narx yorliqlarini chop etish")
        self.resize(760, 700)

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

        # "Nusxalar soni" ustuni torayib ketmasligi uchun aniq kenglik
        # bilan mahkamlanadi (pin_column_width) — qolgan ustunlar
        # (Mahsulot/Narxi/Shtrix kod) qolgan joyni bo'lib oladi.
        # Dialog ham kengroq (760px), shu bilan birga jadval hech
        # qachon spinbox'ni kesib qo'ymaydi.
        self.items_table = DataTable()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Shtrix kod",
            "Nusxalar soni",
        ])
        self.items_table.pin_column_width(_COPIES_COLUMN)
        main_layout.addWidget(self.items_table)

        preview_row = QHBoxLayout()
        preview_row.addStretch()

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("labelPreview")
        self.preview_label.setFixedSize(
            _SHEET_PREVIEW_WIDTH, _SHEET_PREVIEW_HEIGHT
        )
        preview_row.addWidget(self.preview_label)
        preview_row.addStretch()

        main_layout.addLayout(preview_row)

        self.preview_caption = QLabel()
        self.preview_caption.setObjectName("mutedText")
        self.preview_caption.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.preview_caption)

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

            self.items_table.setCellWidget(
                row, _COPIES_COLUMN, copies_spinbox
            )
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

    def update_preview(self):
        entries = self._collect_entries()
        width_mm, height_mm = self.get_label_size_mm()
        cols, rows = compute_grid_layout(width_mm, height_mm)

        pixmap = QPixmap(
            _SHEET_PREVIEW_WIDTH, _SHEET_PREVIEW_HEIGHT
        )
        pixmap.fill(Qt.white)

        if entries:
            pages = paginate_entries(entries, cols, rows)
            first_page = pages[0]

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            paint_label_sheet(
                painter,
                QRectF(0, 0, _SHEET_PREVIEW_WIDTH, _SHEET_PREVIEW_HEIGHT),
                first_page,
                cols,
                width_mm,
                height_mm,
            )
            painter.end()

            per_page = cols * rows
            self.preview_caption.setText(
                f"1-varaq / {len(pages)} varaq — har varaqqa "
                f"{per_page} tagacha yorliq, jami {len(entries)} dona"
            )
        else:
            self.preview_caption.setText(
                "Chop etiladigan yorliq yo'q — nusxalar sonini "
                "tekshiring."
            )

        self.preview_label.setPixmap(pixmap)

    def _collect_entries(self):
        products_with_copies = [
            (product, self._copy_inputs[product.id].value())
            for product in self._products
        ]

        return build_label_entries(products_with_copies)

    def _render_to_printer(self, printer, entries):
        width_mm, height_mm = self.get_label_size_mm()
        cols, rows = compute_grid_layout(width_mm, height_mm)
        pages = paginate_entries(entries, cols, rows)

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for index, page_entries in enumerate(pages):
            if index > 0:
                printer.newPage()

            rect = QRectF(printer.pageRect(QPrinter.DevicePixel))
            paint_label_sheet(
                painter, rect, page_entries, cols, width_mm, height_mm
            )

        painter.end()

        return len(pages)

    def _build_printer(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(
            QPageSize(
                QSizeF(SHEET_WIDTH_MM, SHEET_HEIGHT_MM),
                QPageSize.Millimeter,
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

        # Bitta QPrinter + bitta QPainter sessiyasi — barcha
        # tanlangan mahsulotlar va ularning nusxalari yagona chop
        # etish topshirig'i sifatida yuboriladi, birma-bir emas.
        page_count = self._render_to_printer(printer, entries)

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"{len(entries)} ta yorliq ({page_count} varaqda) "
            "chop etildi.",
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

        # Yagona PDF fayl, ichida bir nechta varaq — har varaqqa
        # yorliq o'lchamiga qarab bir nechta yorliq (panjara).
        page_count = self._render_to_printer(printer, entries)

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"Saqlandi: {file_path}\n"
            f"{len(entries)} ta yorliq, {page_count} varaq.",
        )
