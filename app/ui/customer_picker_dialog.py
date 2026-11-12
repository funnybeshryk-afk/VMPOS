from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScroller,
    QVBoxLayout,
)

from app.services.customer_service import CustomerService
from app.ui.customer_dialog import CustomerDialog
from app.ui.touch_dialog import TouchDialog
from app.utils.amount_buffer import AmountBuffer
from app.utils.formatters import format_money
from app.widgets.badge import StatusBadge, set_badge_variant
from app.widgets.numpad import AmountField, NumPad
from app.widgets.secondary_button import SecondaryButton

_TOLERANCE = 0.01


class CustomerPickerDialog(TouchDialog):
    """Nasiya savdo uchun mavjud mijozlar bazasidan tanlov.

    UserPickerDialog bilan bir xil naqsh (ro'yxat + OK), lekin
    mijozlar soni kassirlar sonidan ancha ko'p bo'lishi mumkin —
    shuning uchun qidiruv maydoni qo'shilgan. Shu yerda yana ikkita
    qo'shimcha imkoniyat bor:

    - "Yangi mijoz qo'shish" — kerakli mijoz bazada yo'q bo'lsa,
      kassir shu yerdan darhol yaratadi (CustomerDialog orqali),
      yangi mijoz avtomatik tanlangan holatga o'tadi.
    - Qarzga yoziladigan summa — odatda chek jamisiga teng, lekin
      qisman naqd + qisman nasiya holatlari uchun kassir pastga
      tushirib o'zgartirishi mumkin (masalan mijoz yarmini naqd
      to'laydi, qolgani qarzga yoziladi).
    """

    def __init__(self, customers, total_amount, parent=None):
        super().__init__("Mijozni tanlash", parent, min_width=900)
        self.resize(940, 660)

        self._customers = list(customers)
        self.total_amount = total_amount

        self._debt_buffer = AmountBuffer(allow_decimal=True, max_decimals=2)
        self._debt_buffer.set_value(total_amount)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 22)
        outer.setSpacing(22)

        # ---- chap: mijozlar ro'yxati (barmoq uchun katta qatorlar) ----
        left = QVBoxLayout()
        left.setSpacing(12)

        info_label = QLabel("Nasiya kimga yoziladi?")
        info_label.setObjectName("entryProduct")

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchInput")
        self.search_edit.setPlaceholderText(
            "Mijoz nomi yoki telefon bo'yicha qidirish..."
        )
        self.search_edit.textChanged.connect(self._apply_filter)

        self.customers_list = QListWidget()
        self.customers_list.setStyleSheet(
            "QListWidget::item { min-height: 64px; padding: 4px 12px; }"
        )
        self.customers_list.itemDoubleClicked.connect(
            lambda _item: self._try_accept()
        )
        QScroller.grabGesture(
            self.customers_list.viewport(), QScroller.TouchGesture
        )

        # Yangi mijoz qo'shish ism/telefon yozishni talab qiladi —
        # bu yerda jismoniy klaviatura kerak (kassir ish jarayonidan
        # tashqari, kamdan-kam amal).
        self.add_customer_button = SecondaryButton("Yangi mijoz qo'shish")
        self.add_customer_button.clicked.connect(self._add_new_customer)

        left.addWidget(info_label)
        left.addWidget(self.search_edit)
        left.addWidget(self.customers_list, 1)
        left.addWidget(self.add_customer_button)

        # ---- o'ng: qarz summasi + raqamli blok -----------------------
        right = QVBoxLayout()
        right.setSpacing(12)

        total_box = QFrame()
        total_box.setObjectName("totalBox")
        total_box.setFixedHeight(76)

        total_caption = QLabel("Chek jamisi")
        total_caption.setObjectName("cartTotalCaption")

        total_amount_label = QLabel(
            f"{format_money(total_amount)} "
            "<span style='font-size:16px;font-weight:500;"
            "color:#a8a29e'>so'm</span>"
        )
        total_amount_label.setObjectName("cartTotalAmount")
        total_amount_label.setTextFormat(Qt.RichText)

        total_row = QHBoxLayout(total_box)
        total_row.setContentsMargins(20, 0, 20, 0)
        total_row.addWidget(total_caption)
        total_row.addStretch()
        total_row.addWidget(total_amount_label)

        self._debt_field = AmountField("Qarzga yoziladigan summa", "so'm")
        self._debt_field.set_active(True)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.addWidget(self.make_chip("Hammasi", lambda: self._set_debt(1)))
        chips.addWidget(self.make_chip("Yarmi", lambda: self._set_debt(0.5)))

        self.cash_hint_badge = StatusBadge("", "neutral")

        pad = NumPad(left_key="000")
        self.connect_numpad(pad)

        right.addWidget(total_box)
        right.addWidget(self._debt_field)
        right.addLayout(chips)
        right.addWidget(
            self.cash_hint_badge, alignment=Qt.AlignCenter
        )
        right.addWidget(pad)
        right.addLayout(self.build_footer("Tasdiqlash"))

        # Tasdiqlash — tekshiruv bilan (mijoz tanlanganmi, summa to'g'rimi).
        self.ok_button.clicked.disconnect()
        self.ok_button.clicked.connect(self._try_accept)

        outer.addLayout(left, 1)
        outer.addLayout(right, 1)

        self._populate(self._customers)
        self.buffer_changed()

    # ---- TouchDialog ---------------------------------------------

    def active_buffer(self):
        return self._debt_buffer

    def buffer_changed(self):
        self._debt_field.set_text(self._debt_buffer.display())
        self._update_cash_hint()

    def _set_debt(self, share):
        self._debt_buffer.set_value(round(self.total_amount * share, 2))
        self.buffer_changed()

    def _populate(self, customers, select_customer_id=None):
        self.customers_list.clear()

        selected_row = 0

        for row, customer in enumerate(customers):
            # Ikki qator: ism (yirik) va pastda telefon / qarz — uzun
            # qator o'ngdan kesilib qolmasin.
            details = []

            if customer.phone:
                details.append(customer.phone)

            if customer.debt_amount > 0:
                details.append(
                    f"qarz: {format_money(customer.debt_amount)} so'm"
                )

            label = customer.name

            if details:
                label += "\n" + " · ".join(details)

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, customer)
            self.customers_list.addItem(item)

            if (
                select_customer_id is not None
                and customer.id == select_customer_id
            ):
                selected_row = row

        if self.customers_list.count() > 0:
            self.customers_list.setCurrentRow(selected_row)

    def _apply_filter(self, text):
        text = text.strip().lower()

        if not text:
            self._populate(self._customers)
            return

        filtered = [
            customer
            for customer in self._customers
            if text in (customer.name or "").lower()
            or text in (customer.phone or "").lower()
        ]
        self._populate(filtered)

    def _add_new_customer(self):
        dialog = CustomerDialog(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        if not data["name"]:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mijoz nomini kiriting.",
            )
            return

        new_customer = CustomerService.create_customer(data)

        self._customers.append(new_customer)
        self.search_edit.clear()
        self._populate(
            self._customers, select_customer_id=new_customer.id
        )

    def _parse_debt_amount(self):
        return self._debt_buffer.value()

    def _update_cash_hint(self):
        debt_amount = self._parse_debt_amount()
        cash_now = self.total_amount - debt_amount

        valid = 0 < debt_amount <= self.total_amount + _TOLERANCE
        self._debt_field.set_state("ok" if valid else "bad")

        if not valid:
            set_badge_variant(
                self.cash_hint_badge,
                "Summa 0 dan katta va chek jamisidan oshmasligi "
                "kerak",
                "danger",
            )
        elif cash_now <= _TOLERANCE:
            set_badge_variant(
                self.cash_hint_badge,
                "Butun summa qarzga yoziladi",
                "neutral",
            )
        else:
            set_badge_variant(
                self.cash_hint_badge,
                f"Hoziroq naqd qabul qilinadi: "
                f"{format_money(cash_now)} so'm",
                "success",
            )

    def _try_accept(self):
        if self.get_selected_customer() is None:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Mijozni tanlang.",
            )
            return

        debt_amount = self._parse_debt_amount()

        if debt_amount <= 0:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Qarzga yoziladigan summa noldan katta bo'lishi "
                "kerak.",
            )
            return

        if debt_amount > self.total_amount + _TOLERANCE:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Qarzga yoziladigan summa chek jamisidan katta "
                "bo'lishi mumkin emas.",
            )
            return

        self.accept()

    def get_selected_customer(self):
        item = self.customers_list.currentItem()

        if item is None:
            return None

        return item.data(Qt.UserRole)

    def get_debt_amount(self):
        return self._parse_debt_amount()
