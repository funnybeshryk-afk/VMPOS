from datetime import datetime

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.customer_service import CustomerService
from app.services.product_service import ProductService
from app.services.sale_service import SaleService
from app.services.shift_service import ShiftService
from app.state.session import get_current_user
from app.ui.customer_picker_dialog import CustomerPickerDialog
from app.ui.mixed_payment_dialog import MixedPaymentDialog
from app.ui.payment_dialog import PaymentDialog
from app.ui.quantity_edit_dialog import QuantityEditDialog
from app.ui.weight_dialog import WeightDialog
from app.utils.formatters import format_money, format_quantity
from app.utils.icons import load_checkable_icon, load_icon
from app.utils.sounds import (
    play_add_sound,
    play_error_sound,
    play_payment_sound,
)
from app.widgets.badge import StatusBadge, stock_status_badge
from app.widgets.category_bar import CategoryBar
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.product_grid import ProductGrid
from app.widgets.secondary_button import SecondaryButton
from app.widgets.shift_status_panel import ShiftStatusPanel
from app.widgets.success_button import SuccessButton

_SHIFT_REFRESH_INTERVAL_MS = 60_000
_VIEW_TOGGLE_ICON_SIZE = 16
_VIEW_TOGGLE_ICON_UNCHECKED = "#64748b"
_VIEW_TOGGLE_ICON_CHECKED = "#ffffff"


class SalePage(QWidget):
    def __init__(self):
        super().__init__()

        self.cart = {}
        self.selected_category = None
        self.current_shift = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchInput")
        self.search_edit.setPlaceholderText(
            "Shtrix-kod yoki nomi bo'yicha qidirish..."
        )
        self.search_edit.textChanged.connect(self.search_products)
        self.search_edit.returnPressed.connect(
            self.add_product_by_barcode
        )

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self._build_view_toggle())

        # Kategoriya bo'yicha tezkor filtr — sensorli ekranda barmoq
        # bilan bosish uchun, qidiruv maydoniga qo'shimcha.
        self.category_bar = CategoryBar()
        self.category_bar.categorySelected.connect(
            self.on_category_selected
        )

        # Panjara (grid) — rasm/ikonka bilan kartochkalar, odatiy
        # ko'rinish. Ro'yxat (list) — avvalgi DataTable, muqobil
        # rejim sifatida saqlanadi (masalan ko'p qatorli ro'yxatni
        # tez ko'rish uchun qulayroq bo'lishi mumkin).
        self.product_grid = ProductGrid()
        self.product_grid.productClicked.connect(self.add_product)

        self.products_table = DataTable()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Shtrix-kod",
            "Mahsulot",
            "Narxi",
            "Qoldiq",
            "Holat",
        ])
        self.products_table.pin_column_width(4)
        self.products_table.cellDoubleClicked.connect(
            self.on_product_double_clicked
        )

        self.products_view_stack = QStackedWidget()
        self.products_view_stack.addWidget(self.product_grid)
        self.products_view_stack.addWidget(self.products_table)

        left_layout.addLayout(search_row)
        left_layout.addWidget(self.category_bar)
        left_layout.addWidget(self.products_view_stack)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Joriy smena plashkasi — kassir kim ekanini va smena
        # ochilganmi-yo'qmi ko'rsatadi. MainWindow buni Moliya
        # sahifasiga o'tish tugmasiga ulaydi (openMoliyaRequested).
        self.shift_panel = ShiftStatusPanel()

        cart_title = QLabel("Korzina")
        cart_title.setObjectName("sectionTitle")

        self.cart_table = DataTable()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Soni",
            "Jami",
        ])
        # "Optom" bejchi bilan narx katakchasi Stretch rejimida
        # torayib, bejchini kesib qo'yishi mumkin. ResizeToContents
        # bu yerda setCellWidget() bilan qo'shilgan murakkab katakcha
        # (matn + bejcha) kengligini ishonchli o'lchamadi, shuning
        # uchun aniq kenglik beriladi — foydalanuvchi kerak bo'lsa
        # qo'lda kengaytirishi mumkin (Interactive).
        self.cart_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Interactive
        )
        self.cart_table.horizontalHeader().resizeSection(1, 190)
        self.cart_table.cellDoubleClicked.connect(
            self.on_cart_item_double_clicked
        )

        self.cart_empty_state = self.build_cart_empty_state()

        # Bo'sh korzina uchun oddiy jadval o'rniga ikonka bilan
        # placeholder ko'rsatiladi — shunday holatda foydalanuvchiga
        # nima qilish kerakligi ko'rinib turadi ("Mahsulot tanlang").
        self.cart_stack = QStackedWidget()
        self.cart_stack.addWidget(self.cart_table)
        self.cart_stack.addWidget(self.cart_empty_state)

        # Ombordan chiqarish/miqdorni o'zgartirish — ikkinchi darajali
        # amallar, shuning uchun SecondaryButton. O'chirish esa
        # korzinadan mahsulotni olib tashlaydi, shu sabab DangerButton.
        self.edit_quantity_button = SecondaryButton(
            "Miqdorni o'zgartirish"
        )
        self.edit_quantity_button.clicked.connect(
            self.edit_selected_quantity
        )

        self.remove_button = DangerButton("Tanlanganni o'chirish")
        self.remove_button.clicked.connect(self.remove_selected_item)

        self.new_sale_button = SecondaryButton("Yangi savdo")
        self.new_sale_button.clicked.connect(self.clear_cart)

        utility_row = QHBoxLayout()
        utility_row.addWidget(self.edit_quantity_button)
        utility_row.addWidget(self.remove_button)
        utility_row.addWidget(self.new_sale_button)

        self.total_label = QLabel("Jami: 0 so'm")
        self.total_label.setObjectName("cartTotal")
        self.total_label.setAlignment(Qt.AlignCenter)

        # To'lovni yakunlash — sahifaning eng ko'p bosiladigan amali.
        # Yagona SuccessButton (yashil) shu yerda: "pul qabul qilindi"
        # degani, xuddi Hisobotlardagi "to'langan" bilan bir xil rangda.
        # Karta va aralash to'lov — kamroq ishlatiladi, shuning uchun
        # SecondaryButton: ular ham bosiladi, lekin ko'zga tashlanmaydi.
        self.cash_payment_button = SuccessButton(
            "Naqd pul bilan to'lash",
            large=True,
        )
        self.cash_payment_button.clicked.connect(
            lambda: self.complete_sale("cash")
        )
        self.cash_payment_button.setIcon(
            load_icon("layers", color="#ffffff")
        )
        self.cash_payment_button.setIconSize(QSize(20, 20))

        self.card_payment_button = SecondaryButton(
            "Karta bilan to'lash",
            large=True,
        )
        self.card_payment_button.clicked.connect(
            lambda: self.complete_sale("card")
        )
        self.card_payment_button.setIcon(
            load_icon("credit-card", color="#334155")
        )
        self.card_payment_button.setIconSize(QSize(20, 20))

        self.mixed_payment_button = SecondaryButton("Aralash to'lov")
        self.mixed_payment_button.clicked.connect(
            lambda: self.complete_sale("mixed")
        )
        self.mixed_payment_button.setIcon(
            load_icon("shuffle", color="#334155")
        )
        self.mixed_payment_button.setIconSize(QSize(16, 16))

        # Nasiya — pul kassaga tushmaydi, mijoz qarziga yoziladi,
        # shuning uchun majburiy mijoz tanlovi bilan (complete_sale
        # ichida). Naqd/Karta/Aralash bilan bir qatorda, lekin
        # ularning eng kam ishlatiladigani sifatida SecondaryButton.
        self.debt_payment_button = SecondaryButton("Nasiya")
        self.debt_payment_button.clicked.connect(
            lambda: self.complete_sale("debt")
        )
        self.debt_payment_button.setIcon(
            load_icon("clock", color="#334155")
        )
        self.debt_payment_button.setIconSize(QSize(16, 16))

        right_layout.addWidget(self.shift_panel)
        right_layout.addWidget(cart_title)
        right_layout.addWidget(self.cart_stack)
        right_layout.addLayout(utility_row)
        right_layout.addWidget(self.total_label)
        right_layout.addWidget(self.cash_payment_button)
        right_layout.addWidget(self.card_payment_button)
        right_layout.addWidget(self.mixed_payment_button)
        right_layout.addWidget(self.debt_payment_button)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setup_shortcuts()
        self.load_products()
        self.update_cart_table()

        # Smena ochilgan/ochilmaganini va soatni sahifa fonda turganda
        # ham yangilab turadi — real vaqt oqimida smena faqat Moliya
        # sahifasiga o'tib ochiladi (bu bitta oynali ilova, bir vaqtda
        # bitta sahifa ko'rinadi), shuning uchun showEvent() allaqachon
        # har safar Sotuv'ga qaytilganda darhol yangilaydi; timer esa
        # shunchaki soatni va smenani sahifa ochiq turgan paytda ham
        # yangilab turish uchun zaxira sifatida ishlaydi.
        self.refresh_shift_panel()

        self._shift_refresh_timer = QTimer(self)
        self._shift_refresh_timer.timeout.connect(
            self.refresh_shift_panel
        )
        self._shift_refresh_timer.start(_SHIFT_REFRESH_INTERVAL_MS)

    def _build_view_toggle(self):
        toggle_row = QWidget()

        toggle_layout = QHBoxLayout(toggle_row)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(2)

        self._view_toggle_group = QButtonGroup(self)
        self._view_toggle_group.setExclusive(True)

        self.grid_view_button = self._make_view_toggle_button(
            "grid", "Katakcha ko'rinishi"
        )
        self.grid_view_button.setChecked(True)
        self.grid_view_button.clicked.connect(
            lambda: self.set_view_mode("grid")
        )

        self.list_view_button = self._make_view_toggle_button(
            "list", "Ro'yxat ko'rinishi"
        )
        self.list_view_button.clicked.connect(
            lambda: self.set_view_mode("list")
        )

        toggle_layout.addWidget(self.grid_view_button)
        toggle_layout.addWidget(self.list_view_button)

        return toggle_row

    def _make_view_toggle_button(self, icon_name, tooltip):
        button = QPushButton()
        button.setObjectName("viewToggleButton")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setIcon(
            load_checkable_icon(
                icon_name,
                _VIEW_TOGGLE_ICON_UNCHECKED,
                _VIEW_TOGGLE_ICON_CHECKED,
                _VIEW_TOGGLE_ICON_SIZE,
            )
        )
        button.setIconSize(
            QSize(_VIEW_TOGGLE_ICON_SIZE, _VIEW_TOGGLE_ICON_SIZE)
        )

        self._view_toggle_group.addButton(button)

        return button

    def set_view_mode(self, mode):
        if mode == "list":
            self.products_view_stack.setCurrentWidget(
                self.products_table
            )
        else:
            self.products_view_stack.setCurrentWidget(
                self.product_grid
            )

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.focus_search)
        self.refresh_shift_panel()

    def refresh_shift_panel(self):
        self.current_shift = ShiftService.get_open_shift()
        now_text = datetime.now().strftime("%d.%m.%Y, %H:%M")

        if self.current_shift is None:
            self.shift_panel.show_no_shift()
        else:
            self.shift_panel.show_shift(
                self.current_shift.cashier_name,
                self.current_shift.id,
                self.current_shift.opened_at,
                now_text,
            )

        self.update_payment_buttons_enabled()

    def update_payment_buttons_enabled(self):
        has_shift = self.current_shift is not None

        self.cash_payment_button.setEnabled(has_shift)
        self.card_payment_button.setEnabled(has_shift)
        self.mixed_payment_button.setEnabled(has_shift)
        self.debt_payment_button.setEnabled(has_shift)

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

        self.selected_category = None
        self.category_bar.set_categories(
            self.get_distinct_categories()
        )

        self.search_products(self.search_edit.text())

    def get_distinct_categories(self):
        categories = {
            product.category.strip()
            for product in self.products
            if product.category and product.category.strip()
        }

        return sorted(categories)

    def on_category_selected(self, category):
        self.selected_category = category
        self.search_products(self.search_edit.text())

    def populate_products(self, products):
        self.product_grid.set_products(products)
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
            self.products_table.setCellWidget(
                row,
                4,
                stock_status_badge(
                    product.quantity,
                    product.min_quantity,
                ),
            )

    def search_products(self, text):
        text = text.strip().lower()
        filtered = []

        for product in self.products:
            if self.selected_category:
                category = (product.category or "").strip()

                if category != self.selected_category:
                    continue

            if text:
                barcode = (product.barcode or "").lower()
                name = (product.name or "").lower()

                if text not in barcode and text not in name:
                    continue

            filtered.append(product)

        self.populate_products(filtered)

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

        if product.quantity <= 0:
            play_error_sound()

            QMessageBox.warning(
                self,
                "Diqqat",
                f"Qoldiq yo'q: {product.name}",
            )
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

        # Ehtiyot chorasi: yuqorida add_product() nolinchi qoldiqni
        # allaqachon to'xtatadi, lekin bu yerda ham tekshiruv qoldiq —
        # korzinada 0 miqdorli qator hech qachon paydo bo'lmasligi kerak.
        if quantity <= 0:
            return

        quantity_in_cart = 0

        if product_id in self.cart:
            quantity_in_cart = self.cart[product_id]["quantity"]

        new_quantity = quantity_in_cart + quantity

        if new_quantity > product.quantity:
            play_error_sound()

            QMessageBox.warning(
                self,
                "Diqqat",
                f"Qoldiq yetarli emas: {product.name}",
            )
            return

        unit_price, is_wholesale = self.resolve_cart_pricing(
            product, new_quantity
        )

        self.cart[product_id] = {
            "product": product,
            "quantity": new_quantity,
            "unit_price": unit_price,
            "is_wholesale": is_wholesale,
        }

        self.update_cart_table()
        play_add_sound()

    def resolve_cart_pricing(self, product, quantity):
        """Berilgan miqdor uchun birlik narxi va u optommi-yo'qmi.

        Miqdor o'zgarganda (qo'shilganda yoki tahrirlanganda) har
        safar shu yerdan chaqiriladi — mos optom daraja avtomatik
        qo'llanadi, kassir alohida hech narsa tanlamaydi.
        """

        unit_price = ProductService.resolve_price(product, quantity)
        is_wholesale = unit_price != product.sell_price

        return unit_price, is_wholesale

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

        new_quantity = dialog.get_quantity()
        unit_price, is_wholesale = self.resolve_cart_pricing(
            product, new_quantity
        )

        self.cart[product_id]["quantity"] = new_quantity
        self.cart[product_id]["unit_price"] = unit_price
        self.cart[product_id]["is_wholesale"] = is_wholesale

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
            total += item["unit_price"] * item["quantity"]

        return total

    def _pick_debt_customer(self, total_amount):
        """Nasiya uchun mijoz va qarzga yoziladigan summa tanlovi.

        Dialogda mijozlar bazasi bo'sh bo'lsa ham "Yangi mijoz
        qo'shish" orqali darhol yaratish mumkin, shuning uchun bu
        yerda bo'sh bazani alohida to'xtatib qo'ymaymiz. Bekor
        qilinsa (yoki dialog ichidagi tekshiruv o'tmasa) (None, None)
        qaytadi — chaqiruvchi complete_sale butun savdoni bekor
        qiladi, chunki Nasiya mijozsiz yoki noto'g'ri summada
        ma'nosiz.
        """

        customers = CustomerService.get_all_customers()

        dialog = CustomerPickerDialog(customers, total_amount, self)

        if not dialog.exec():
            return None, None

        customer = dialog.get_selected_customer()

        if customer is None:
            return None, None

        return customer, dialog.get_debt_amount()

    def complete_sale(self, payment_method=None):
        # Tugmalar smena yopiq bo'lsa disabled bo'ladi, lekin F4
        # klaviatura yorlig'i tugma holatidan mustaqil ishlaydi —
        # shuning uchun bu yerda ham tekshiramiz.
        if self.current_shift is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Sotish uchun avval Moliya bo'limida smenani "
                "oching.",
            )
            return

        if not self.cart:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Korzina bo'sh.",
            )
            return

        total_amount = self.calculate_cart_total()

        cash_amount = None
        card_amount = None
        customer_id = None
        debt_amount = None

        if payment_method == "debt":
            customer, debt_amount = self._pick_debt_customer(
                total_amount
            )

            if customer is None:
                return

            customer_id = customer.id
            paid_amount = total_amount - debt_amount

        elif payment_method == "mixed":
            mixed_dialog = MixedPaymentDialog(total_amount, self)

            if not mixed_dialog.exec():
                return

            cash_amount, card_amount = (
                mixed_dialog.get_payment_data()
            )
            paid_amount = cash_amount + card_amount

        elif payment_method == "card":
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

        current_user = get_current_user()
        cashier_name = (
            current_user.full_name if current_user else None
        )
        cashier_user_id = current_user.id if current_user else None

        try:
            sale = SaleService.create_sale(
                self.cart,
                payment_method,
                paid_amount,
                cash_amount,
                card_amount,
                customer_id=customer_id,
                cashier_name=cashier_name,
                cashier_user_id=cashier_user_id,
                debt_amount=debt_amount,
                shift_id=(
                    self.current_shift.id
                    if self.current_shift
                    else None
                ),
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
        play_payment_sound()

        if payment_method == "debt":
            result_text = (
                f"Savdo #{sale.id} muvaffaqiyatli saqlandi.\n"
                f"Qarzga yozildi: {format_money(debt_amount)} so'm\n"
                f"Hoziroq naqd qabul qilindi: "
                f"{format_money(sale.paid_amount)} so'm"
            )
        else:
            result_text = (
                f"Savdo #{sale.id} muvaffaqiyatli saqlandi.\n"
                f"Qaytim: {format_money(sale.change_amount)} so'm"
            )

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            result_text,
        )

    def build_cart_empty_state(self):
        widget = QWidget()

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setPixmap(
            load_icon(
                "shopping-cart", color="#94a3b8", size=48
            ).pixmap(QSize(48, 48))
        )
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Savat bo'sh")
        title_label.setObjectName("cartEmptyTitle")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Mahsulot tanlang")
        subtitle_label.setObjectName("cartEmptySubtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return widget

    def build_price_cell(self, unit_price, is_wholesale):
        """Narx + (agar optom qo'llanilgan bo'lsa) "Optom" bejchi.

        Kassir buni ko'rib, narx o'zi adashib emas, avtomatik
        qoidaga ko'ra qo'llanilganini bilishi uchun.
        """

        cell = QWidget()
        # badge_cell'dagi kabi — sichqoncha voqealari qatorni
        # tanlash/qo'sh bosishga to'sqinlik qilmasligi kerak.
        cell.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout = QHBoxLayout(cell)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        price_label = QLabel(f"{format_money(unit_price)} so'm")

        layout.addWidget(price_label)

        if is_wholesale:
            layout.addWidget(StatusBadge("Optom", "success"))

        layout.addStretch()

        return cell

    def update_cart_table(self):
        self.cart_stack.setCurrentWidget(
            self.cart_table if self.cart else self.cart_empty_state
        )

        self.cart_table.setRowCount(len(self.cart))

        for row, (product_id, item) in enumerate(self.cart.items()):
            product = item["product"]
            quantity = item["quantity"]
            unit_price = item["unit_price"]
            is_wholesale = item["is_wholesale"]
            line_total = unit_price * quantity

            product_item = QTableWidgetItem(product.name)
            product_item.setData(Qt.UserRole, product_id)

            self.cart_table.setItem(row, 0, product_item)
            self.cart_table.setCellWidget(
                row,
                1,
                self.build_price_cell(unit_price, is_wholesale),
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