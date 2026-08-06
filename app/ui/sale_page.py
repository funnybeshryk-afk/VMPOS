from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.product_service import ProductService
from app.services.sale_service import SaleService
from app.ui.payment_dialog import PaymentDialog
from app.ui.quantity_edit_dialog import QuantityEditDialog
from app.ui.weight_dialog import WeightDialog
from app.utils.formatters import format_money, format_quantity
from app.utils.sounds import play_error_sound, play_success_sound


class SalePage(QWidget):
    def __init__(self):
        super().__init__()

        self.cart = {}

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Mahsulot qidirish...")
        self.search_edit.textChanged.connect(self.search_products)
        self.search_edit.returnPressed.connect(
            self.add_product_by_barcode
        )

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels([
            "Shtrix-kod",
            "Mahsulot",
            "Narxi",
            "Qoldiq",
        ])
        self.products_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.products_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.products_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.products_table.cellDoubleClicked.connect(
            self.on_product_double_clicked
        )

        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.products_table)

        right_layout = QVBoxLayout()

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Soni",
            "Jami",
        ])
        self.cart_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.cart_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.cart_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.cart_table.cellDoubleClicked.connect(
            self.on_cart_item_double_clicked
        )

        self.edit_quantity_button = QPushButton(
            "Miqdorni o'zgartirish"
        )
        self.edit_quantity_button.clicked.connect(
            self.edit_selected_quantity
        )

        self.remove_button = QPushButton("Tanlanganni o'chirish")
        self.remove_button.clicked.connect(self.remove_selected_item)

        self.new_sale_button = QPushButton("Yangi savdo")
        self.new_sale_button.clicked.connect(self.clear_cart)

        self.cash_payment_button = QPushButton(
            "Naqd pul bilan to'lash"
        )
        self.cash_payment_button.clicked.connect(
            lambda: self.complete_sale("cash")
        )
        self.cash_payment_button.setStyleSheet(
            """
            background-color: #2e7d32;
            color: white;
            font-size: 16px;
            font-weight: 700;
            min-height: 42px;
            border-radius: 7px;
            """
        )

        self.card_payment_button = QPushButton(
            "Karta bilan to'lash"
        )
        self.card_payment_button.clicked.connect(
            lambda: self.complete_sale("card")
        )
        self.card_payment_button.setStyleSheet(
            """
            background-color: #1565c0;
            color: white;
            font-size: 16px;
            font-weight: 700;
            min-height: 42px;
            border-radius: 7px;
            """
        )

        self.mixed_payment_button = QPushButton("Aralash to'lov")
        self.mixed_payment_button.clicked.connect(self.complete_sale)
        self.mixed_payment_button.setStyleSheet(
            """
            background-color: #ef6c00;
            color: white;
            font-size: 15px;
            font-weight: 700;
            min-height: 38px;
            border-radius: 7px;
            """
        )

        self.total_label = QLabel("Jami: 0 so'm")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setMinimumHeight(72)
        self.total_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: 700;
            color: white;
            background-color: #2e7d32;
            border-radius: 8px;
            padding: 10px;
            """
        )

        right_layout.addWidget(self.cart_table)
        right_layout.addWidget(self.edit_quantity_button)
        right_layout.addWidget(self.remove_button)
        right_layout.addWidget(self.new_sale_button)
        right_layout.addWidget(self.cash_payment_button)
        right_layout.addWidget(self.card_payment_button)
        right_layout.addWidget(self.mixed_payment_button)
        right_layout.addWidget(self.total_label)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setup_shortcuts()
        self.load_products()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.focus_search)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("F2"), self, self.focus_search)
        QShortcut(QKeySequence("F4"), self, self.complete_sale)
        QShortcut(QKeySequence("F5"), self, self.clear_cart)
        QShortcut(
            QKeySequence(Qt.Key_Delete),
            self,
            self.remove_selected_item,
        )
        QShortcut(
            QKeySequence(Qt.Key_Escape),
            self,
            self.clear_search,
        )

    def focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def clear_search(self):
        self.search_edit.clear()
        self.search_edit.setFocus()

    def load_products(self):
        self.products = ProductService.get_all_products()
        self.search_products(self.search_edit.text())

    def populate_table(self, products):
        self.products_table.setRowCount(len(products))

        for row, product in enumerate(products):
            barcode_item = QTableWidgetItem(product.barcode)
            barcode_item.setData(Qt.UserRole, product.id)

            self.products_table.setItem(row, 0, barcode_item)
            self.products_table.setItem(
                row, 1, QTableWidgetItem(product.name)
            )
            self.products_table.setItem(
                row,
                2,
                QTableWidgetItem(format_money(product.sell_price)),
            )
            self.products_table.setItem(
                row,
                3,
                QTableWidgetItem(format_quantity(product.quantity)),
            )

    def search_products(self, text):
        text = text.strip().lower()

        if not text:
            self.populate_table(self.products)
            return

        filtered = []

        for product in self.products:
            barcode = product.barcode.lower() if product.barcode else ""
            name = product.name.lower() if product.name else ""

            if text in barcode or text in name:
                filtered.append(product)

        self.populate_table(filtered)

    def is_weight_product(self, product):
        unit = (product.unit or "").strip().lower()

        return unit in {"kg", "кг"}

    def add_product_by_barcode(self):
        barcode = self.search_edit.text().strip()

        if not barcode:
            return

        for product in self.products:
            if product.barcode == barcode:
                self.add_product(product.id)
                self.search_edit.clear()
                return

        play_error_sound()

        QMessageBox.warning(
            self,
            "Diqqat",
            "Mahsulot topilmadi.",
        )
        self.search_edit.selectAll()

    def on_product_double_clicked(self, row, column):
        item = self.products_table.item(row, 0)

        if item is None:
            return

        self.add_product(item.data(Qt.UserRole))

    def on_cart_item_double_clicked(self, row, column):
        self.cart_table.selectRow(row)
        self.edit_selected_quantity()

    def add_product(self, product_id):
        product = None

        for current_product in self.products:
            if current_product.id == product_id:
                product = current_product
                break

        if product is None:
            return

        if self.is_weight_product(product):
            dialog = WeightDialog(product, self)

            if not dialog.exec():
                return

            quantity = dialog.get_weight()
        else:
            quantity = 1

        self.add_to_cart(product_id, quantity)

    def add_to_cart(self, product_id, quantity):
        product = None

        for current_product in self.products:
            if current_product.id == product_id:
                product = current_product
                break

        if product is None:
            return

        quantity_in_cart = 0

        if product_id in self.cart:
            quantity_in_cart = self.cart[product_id]["quantity"]

        if quantity_in_cart + quantity > product.quantity:
            play_error_sound()

            QMessageBox.warning(
                self,
                "Diqqat",
                f"Qoldiq yetarli emas: {product.name}",
            )
            return

        if product_id in self.cart:
            self.cart[product_id]["quantity"] += quantity
        else:
            self.cart[product_id] = {
                "product": product,
                "quantity": quantity,
            }

        self.update_cart_table()
        play_success_sound()

    def get_selected_product_id(self):
        selected_items = self.cart_table.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)

    def edit_selected_quantity(self):
        product_id = self.get_selected_product_id()

        if product_id not in self.cart:
            return

        item = self.cart[product_id]
        product = item["product"]

        dialog = QuantityEditDialog(
            product,
            item["quantity"],
            self,
        )

        if not dialog.exec():
            return

        self.cart[product_id]["quantity"] = dialog.get_quantity()
        self.update_cart_table()

    def remove_selected_item(self):
        product_id = self.get_selected_product_id()

        if product_id not in self.cart:
            return

        del self.cart[product_id]
        self.update_cart_table()

    def clear_cart(self):
        self.cart.clear()
        self.update_cart_table()
        self.focus_search()

    def calculate_cart_total(self):
        total = 0

        for item in self.cart.values():
            product = item["product"]
            quantity = item["quantity"]

            total += product.sell_price * quantity

        return total

    def complete_sale(self, payment_method=None):
        if not self.cart:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Korzina bo'sh.",
            )
            return

        total_amount = self.calculate_cart_total()

        if payment_method == "card":
            paid_amount = total_amount
        else:
            payment_dialog = PaymentDialog(
                total_amount,
                payment_method,
                self,
            )

            if not payment_dialog.exec():
                return

            payment_method, paid_amount = (
                payment_dialog.get_payment_data()
            )

        try:
            sale = SaleService.create_sale(
                self.cart,
                payment_method,
                paid_amount,
            )

        except ValueError as error:
            play_error_sound()

            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        except Exception:
            play_error_sound()

            QMessageBox.critical(
                self,
                "Xatolik",
                "Savdoni saqlashda xatolik yuz berdi.",
            )
            return

        self.clear_cart()
        self.load_products()
        play_success_sound()

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"Savdo #{sale.id} muvaffaqiyatli saqlandi.\n"
            f"Qaytim: {format_money(sale.change_amount)} so'm",
        )

    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))

        for row, (product_id, item) in enumerate(self.cart.items()):
            product = item["product"]
            quantity = item["quantity"]
            line_total = product.sell_price * quantity

            product_item = QTableWidgetItem(product.name)
            product_item.setData(Qt.UserRole, product_id)

            self.cart_table.setItem(row, 0, product_item)
            self.cart_table.setItem(
                row,
                1,
                QTableWidgetItem(format_money(product.sell_price)),
            )
            self.cart_table.setItem(
                row,
                2,
                QTableWidgetItem(format_quantity(quantity)),
            )
            self.cart_table.setItem(
                row,
                3,
                QTableWidgetItem(format_money(line_total)),
            )

        total = self.calculate_cart_total()
        self.total_label.setText(
            f"Jami: {format_money(total)} so'm"
        )