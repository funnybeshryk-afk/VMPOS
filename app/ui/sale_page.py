from PySide6.QtCore import Qt
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
from app.utils.formatters import format_money, format_quantity


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

        self.decrease_button = QPushButton("1 ta kamaytirish")
        self.decrease_button.clicked.connect(self.decrease_selected_item)

        self.remove_button = QPushButton("Tanlanganni o'chirish")
        self.remove_button.clicked.connect(self.remove_selected_item)

        self.new_sale_button = QPushButton("Yangi savdo")
        self.new_sale_button.clicked.connect(self.clear_cart)

        self.complete_sale_button = QPushButton("Savdoni yakunlash")
        self.complete_sale_button.clicked.connect(self.complete_sale)

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
        right_layout.addWidget(self.decrease_button)
        right_layout.addWidget(self.remove_button)
        right_layout.addWidget(self.new_sale_button)
        right_layout.addWidget(self.complete_sale_button)
        right_layout.addWidget(self.total_label)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.load_products()

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

    def add_product_by_barcode(self):
        barcode = self.search_edit.text().strip()

        if not barcode:
            return

        for product in self.products:
            if product.barcode == barcode:
                self.add_to_cart(product.id)
                self.search_edit.clear()
                return

    def on_product_double_clicked(self, row, column):
        item = self.products_table.item(row, 0)

        if item is None:
            return

        product_id = item.data(Qt.UserRole)
        self.add_to_cart(product_id)

    def add_to_cart(self, product_id):
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

        if quantity_in_cart >= product.quantity:
            QMessageBox.warning(
                self,
                "Diqqat",
                f"Qoldiq yetarli emas: {product.name}",
            )
            return

        if product_id in self.cart:
            self.cart[product_id]["quantity"] += 1
        else:
            self.cart[product_id] = {
                "product": product,
                "quantity": 1,
            }

        self.update_cart_table()

    def get_selected_product_id(self):
        selected_items = self.cart_table.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)

    def decrease_selected_item(self):
        product_id = self.get_selected_product_id()

        if product_id not in self.cart:
            return

        self.cart[product_id]["quantity"] -= 1

        if self.cart[product_id]["quantity"] == 0:
            del self.cart[product_id]

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

    def calculate_cart_total(self):
        total = 0

        for item in self.cart.values():
            product = item["product"]
            quantity = item["quantity"]

            total += product.sell_price * quantity

        return total

    def complete_sale(self):
        if not self.cart:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Korzina bo'sh.",
            )
            return

        total_amount = self.calculate_cart_total()

        payment_dialog = PaymentDialog(total_amount, self)

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
            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        except Exception:
            QMessageBox.critical(
                self,
                "Xatolik",
                "Savdoni saqlashda xatolik yuz berdi.",
            )
            return

        self.clear_cart()
        self.load_products()

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