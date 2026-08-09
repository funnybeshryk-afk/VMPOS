from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from app.services.customer_service import CustomerService
from app.ui.customer_dialog import CustomerDialog
from app.utils.formatters import format_money, parse_number
from app.widgets.badge import StatusBadge, set_badge_variant
from app.widgets.secondary_button import SecondaryButton

_TOLERANCE = 0.01


class CustomerPickerDialog(QDialog):
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
        super().__init__(parent)

        self._customers = list(customers)
        self.total_amount = total_amount

        self.setWindowTitle("Mijozni tanlash")
        self.setMinimumWidth(380)
        self.resize(380, 520)

        main_layout = QVBoxLayout(self)

        info_label = QLabel("Nasiya kimga yoziladi?")
        info_label.setObjectName("sectionTitle")

        total_label = QLabel(
            f"Chek jamisi: {format_money(total_amount)} so'm"
        )
        total_label.setObjectName("cartTotal")
        total_label.setAlignment(Qt.AlignCenter)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchInput")
        self.search_edit.setPlaceholderText(
            "Mijoz nomi yoki telefon bo'yicha qidirish..."
        )
        self.search_edit.textChanged.connect(self._apply_filter)

        self.customers_list = QListWidget()
        self.customers_list.itemDoubleClicked.connect(self.accept)

        self.add_customer_button = SecondaryButton(
            "Yangi mijoz qo'shish"
        )
        self.add_customer_button.clicked.connect(
            self._add_new_customer
        )

        form_layout = QFormLayout()

        self.debt_amount_edit = QLineEdit()
        self.debt_amount_edit.setText(format_money(total_amount))
        self.debt_amount_edit.setPlaceholderText(
            "Masalan: 50 000"
        )
        self.debt_amount_edit.textChanged.connect(
            self._update_cash_hint
        )

        form_layout.addRow(
            "Qarzga yoziladigan summa:", self.debt_amount_edit
        )

        self.cash_hint_badge = StatusBadge("", "neutral")

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(info_label)
        main_layout.addWidget(total_label)
        main_layout.addWidget(self.search_edit)
        main_layout.addWidget(self.customers_list)
        main_layout.addWidget(self.add_customer_button)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(
            self.cash_hint_badge,
            alignment=Qt.AlignCenter,
        )
        main_layout.addWidget(buttons)

        self._populate(self._customers)
        self._update_cash_hint()
        self.search_edit.setFocus()

    def _populate(self, customers, select_customer_id=None):
        self.customers_list.clear()

        selected_row = 0

        for row, customer in enumerate(customers):
            label = customer.name

            if customer.phone:
                label += f" — {customer.phone}"

            if customer.debt_amount > 0:
                label += (
                    f" (qarz: {format_money(customer.debt_amount)} "
                    "so'm)"
                )

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
        try:
            return parse_number(self.debt_amount_edit.text())
        except ValueError:
            return 0

    def _update_cash_hint(self):
        debt_amount = self._parse_debt_amount()
        cash_now = self.total_amount - debt_amount

        if debt_amount <= 0 or debt_amount > (
            self.total_amount + _TOLERANCE
        ):
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
