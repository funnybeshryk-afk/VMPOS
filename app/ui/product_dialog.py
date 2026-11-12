from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.utils.formatters import (
    format_money,
    format_quantity,
    parse_number,
)
from app.utils.icons import load_icon
from app.utils.paths import resolve_data_path
from app.widgets.secondary_button import SecondaryButton

_REMOVE_ICON_SIZE = 14
_REMOVE_ICON_COLOR = "#78716c"

_IMAGE_PREVIEW_SIZE = 72
_IMAGE_FILE_FILTER = (
    "Rasmlar (*.png *.jpg *.jpeg *.webp *.bmp)"
)


class ProductDialog(QDialog):
    def __init__(self, product=None, price_tiers=None):
        super().__init__()

        self.setWindowTitle("Yangi mahsulot")
        self.resize(480, 680)

        layout = QFormLayout(self)

        self._selected_image_source_path = None
        self._remove_image = False

        layout.addRow("Rasm", self._build_photo_row(product))

        self.barcode = QLineEdit()
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.buy_price = QLineEdit()
        self.sell_price = QLineEdit()
        self.unit = QLineEdit()
        self.quantity = QLineEdit()
        self.min_quantity = QLineEdit()
        self.description = QTextEdit()

        # Fiskal ma'lumotlar (soliq chekida talab qilinadi).
        self.ikpu_code = QLineEdit()
        self.package_code = QLineEdit()
        self.vat_rate = QLineEdit()

        self.ikpu_code.setPlaceholderText("IKPU (MXIK) kodi — faqat raqamlar")
        self.package_code.setPlaceholderText("Qadoq kodi — faqat raqamlar")
        self.vat_rate.setPlaceholderText("Bo'sh = do'konning standart stavkasi")

        self.buy_price.setPlaceholderText("Masalan: 15 000,50")
        self.sell_price.setPlaceholderText("Masalan: 18 000")
        self.quantity.setPlaceholderText("Masalan: 10 yoki 0,5")
        self.min_quantity.setPlaceholderText("Masalan: 2")

        if product:
            self.barcode.setText(product.barcode or "")
            self.name.setText(product.name or "")
            self.category.setText(product.category or "")
            self.buy_price.setText(format_money(product.buy_price))
            self.sell_price.setText(format_money(product.sell_price))
            self.unit.setText(product.unit or "")
            self.quantity.setText(
                format_quantity(product.quantity)
            )
            self.min_quantity.setText(
                format_quantity(product.min_quantity)
            )
            self.description.setPlainText(product.description or "")
            self.ikpu_code.setText(product.ikpu_code or "")
            self.package_code.setText(product.package_code or "")

            if product.vat_rate is not None:
                self.vat_rate.setText(f"{product.vat_rate:g}")

        layout.addRow("Shtrix kod", self.barcode)
        layout.addRow("Nomi", self.name)
        layout.addRow("Kategoriya", self.category)
        layout.addRow("Sotib olish narxi", self.buy_price)
        layout.addRow("Sotish narxi", self.sell_price)
        layout.addRow("Birlik", self.unit)
        layout.addRow("Qoldiq", self.quantity)
        layout.addRow("Minimal qoldiq", self.min_quantity)
        layout.addRow("IKPU kodi", self.ikpu_code)
        layout.addRow("Qadoq kodi", self.package_code)
        layout.addRow("QQS stavkasi, %", self.vat_rate)

        # Optom narxlar — ixtiyoriy. Odatda mahsulotda bitta ham
        # qator yo'q, bu holda oddiy sotish narxi doim qo'llanadi.
        # Buyurtmachining o'zi qaysi mahsulotga daraja qo'yishni
        # tanlaydi.
        self._price_tier_rows = []

        price_tiers_section = QWidget()
        price_tiers_section_layout = QVBoxLayout(price_tiers_section)
        price_tiers_section_layout.setContentsMargins(0, 4, 0, 4)
        price_tiers_section_layout.setSpacing(6)

        self.price_tiers_rows_layout = QVBoxLayout()
        self.price_tiers_rows_layout.setSpacing(6)

        add_price_tier_button = SecondaryButton(
            "+ Optom narx qo'shish"
        )
        add_price_tier_button.clicked.connect(
            lambda: self._add_price_tier_row()
        )

        price_tiers_section_layout.addLayout(
            self.price_tiers_rows_layout
        )
        price_tiers_section_layout.addWidget(add_price_tier_button)

        layout.addRow("Optom narxlar", price_tiers_section)

        for tier in price_tiers or []:
            self._add_price_tier_row(
                format_quantity(tier.min_quantity),
                format_money(tier.price),
            )

        layout.addRow("Tavsif", self.description)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def _build_photo_row(self, product):
        row = QWidget()

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        self.image_preview_label = QLabel()
        self.image_preview_label.setObjectName("productImagePreview")
        self.image_preview_label.setFixedSize(
            _IMAGE_PREVIEW_SIZE, _IMAGE_PREVIEW_SIZE
        )
        self.image_preview_label.setAlignment(Qt.AlignCenter)

        buttons_column = QVBoxLayout()
        buttons_column.setSpacing(6)

        select_image_button = SecondaryButton("Rasmni tanlash")
        select_image_button.clicked.connect(self._choose_image)

        remove_image_button = SecondaryButton(
            "Rasmni olib tashlash"
        )
        remove_image_button.clicked.connect(self._clear_image)

        buttons_column.addWidget(select_image_button)
        buttons_column.addWidget(remove_image_button)

        row_layout.addWidget(self.image_preview_label)
        row_layout.addLayout(buttons_column)
        row_layout.addStretch()

        if product and product.image_path:
            self._update_image_preview(
                str(resolve_data_path(product.image_path))
            )
        else:
            self._show_empty_image_preview()

        return row

    def _choose_image(self):
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Rasmni tanlash",
            "",
            _IMAGE_FILE_FILTER,
        )

        if not file_path:
            return

        self._selected_image_source_path = file_path
        self._remove_image = False
        self._update_image_preview(file_path)

    def _clear_image(self):
        self._selected_image_source_path = None
        self._remove_image = True
        self._show_empty_image_preview()

    def _update_image_preview(self, path):
        pixmap = QPixmap(path)

        if pixmap.isNull():
            self._show_empty_image_preview()
            return

        self.image_preview_label.setPixmap(
            pixmap.scaled(
                _IMAGE_PREVIEW_SIZE,
                _IMAGE_PREVIEW_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _show_empty_image_preview(self):
        self.image_preview_label.setPixmap(QPixmap())
        self.image_preview_label.setText("Rasm yo'q")

    def _add_price_tier_row(
        self, min_quantity_text="", price_text=""
    ):
        row_widget = QWidget()

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        min_quantity_edit = QLineEdit(min_quantity_text)
        min_quantity_edit.setPlaceholderText("Miqdor")
        min_quantity_edit.setFixedWidth(70)

        price_edit = QLineEdit(price_text)
        price_edit.setPlaceholderText("Narx")

        remove_button = QPushButton()
        remove_button.setIcon(
            load_icon(
                "x",
                color=_REMOVE_ICON_COLOR,
                size=_REMOVE_ICON_SIZE,
            )
        )
        remove_button.setIconSize(
            QSize(_REMOVE_ICON_SIZE, _REMOVE_ICON_SIZE)
        )
        remove_button.setFixedWidth(28)
        remove_button.setCursor(Qt.PointingHandCursor)
        remove_button.clicked.connect(
            lambda: self._remove_price_tier_row(row_widget)
        )

        row_layout.addWidget(min_quantity_edit)
        row_layout.addWidget(QLabel("donadan →"))
        row_layout.addWidget(price_edit, 1)
        row_layout.addWidget(QLabel("so'm"))
        row_layout.addWidget(remove_button)

        self.price_tiers_rows_layout.addWidget(row_widget)

        self._price_tier_rows.append({
            "widget": row_widget,
            "min_quantity_edit": min_quantity_edit,
            "price_edit": price_edit,
        })

    def _remove_price_tier_row(self, row_widget):
        self._price_tier_rows = [
            row
            for row in self._price_tier_rows
            if row["widget"] is not row_widget
        ]

        self.price_tiers_rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()

    def get_price_tiers_data(self):
        price_tiers = []

        for row in self._price_tier_rows:
            min_quantity_text = row["min_quantity_edit"].text().strip()
            price_text = row["price_edit"].text().strip()

            if not min_quantity_text and not price_text:
                continue

            price_tiers.append({
                "min_quantity": parse_number(min_quantity_text),
                "price": parse_number(price_text),
            })

        return price_tiers

    def get_data(self):
        return {
            "barcode": self.barcode.text(),
            "name": self.name.text(),
            "category": self.category.text(),
            "buy_price": parse_number(self.buy_price.text()),
            "sell_price": parse_number(self.sell_price.text()),
            "unit": self.unit.text(),
            "quantity": parse_number(self.quantity.text()),
            "min_quantity": parse_number(
                self.min_quantity.text()
            ),
            "description": self.description.toPlainText(),
            "ikpu_code": self.ikpu_code.text(),
            "package_code": self.package_code.text(),
            # Bo'sh -> None: do'konning standart QQS stavkasi qo'llanadi.
            "vat_rate": self.vat_rate.text().strip() or None,
            "price_tiers": self.get_price_tiers_data(),
            "image_source_path": self._selected_image_source_path,
            "remove_image": self._remove_image,
        }
