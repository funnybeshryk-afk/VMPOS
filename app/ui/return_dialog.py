from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.product_service import ProductService
from app.services.refund_service import RefundService
from app.services.sale_service import SaleService
from app.state.session import get_current_user
from app.utils.formatters import format_money, format_quantity
from app.widgets.badge import badge_cell, resolve_sale_status
from app.widgets.danger_button import DangerButton
from app.widgets.data_table import DataTable
from app.widgets.primary_button import PrimaryButton
from app.widgets.secondary_button import SecondaryButton


class ReturnDialog(QDialog):
    """Tovarni qaytarish — chekni topib, qatorlarini (to'liq yoki
    qisman) tanlab qaytarish.

    Ikki kirish nuqtasi bor: agar `sale` berilgan bo'lsa (masalan
    SaleDetailsDialog'dan "Qaytarish" bosilganda), qidiruv qismi
    yashiriladi va shu chek darhol yuklanadi. `sale=None` bo'lsa
    (Hisobotlar sahifasidagi mustaqil "Qaytarish" tugmasi), kassir
    chek raqami yoki sana bo'yicha o'zi qidiradi.
    """

    refundCompleted = Signal()

    def __init__(self, sale=None, parent=None):
        super().__init__(parent)

        self._results = {}
        self._sale = None
        self._sale_items = []
        self._row_inputs = {}

        self.setWindowTitle("Tovarni qaytarish")
        self.resize(760, 620)

        main_layout = QVBoxLayout(self)

        self.search_container = self._build_search_row()
        main_layout.addWidget(self.search_container)

        self.results_table = DataTable()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Chek raqami",
            "Sana",
            "Jami",
            "Holat",
        ])
        self.results_table.pin_column_width(3)
        self.results_table.setMaximumHeight(160)
        self.results_table.cellClicked.connect(
            self.on_result_selected
        )
        main_layout.addWidget(self.results_table)

        self.sale_info_label = QLabel("Chek tanlanmagan")
        self.sale_info_label.setObjectName("sectionTitle")
        main_layout.addWidget(self.sale_info_label)

        self.items_table = DataTable()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Sotilgan",
            "Qaytarilgan",
            "Qoldiq",
            "Qaytariladigan",
        ])
        main_layout.addWidget(self.items_table)

        action_row = QHBoxLayout()

        self.select_all_button = SecondaryButton(
            "Hammasini qaytarish"
        )
        self.select_all_button.clicked.connect(
            self.fill_max_quantities
        )

        action_row.addWidget(self.select_all_button)
        action_row.addStretch()

        main_layout.addLayout(action_row)

        self.total_refund_label = QLabel(
            "Qaytariladigan summa: 0 so'm"
        )
        self.total_refund_label.setObjectName("cartTotal")
        self.total_refund_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.total_refund_label)

        self.confirm_button = DangerButton(
            "Qaytarishni tasdiqlash", large=True
        )
        self.confirm_button.clicked.connect(self.confirm_refund)
        self.confirm_button.setEnabled(False)
        main_layout.addWidget(self.confirm_button)

        close_button = SecondaryButton("Yopish")
        close_button.clicked.connect(self.reject)
        main_layout.addWidget(close_button)

        if sale is not None:
            self.search_container.hide()
            self.results_table.hide()
            self.load_sale(sale)
        else:
            self.search()

    def _build_search_row(self):
        container = QWidget()

        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        self.receipt_number_edit = QLineEdit()
        self.receipt_number_edit.setPlaceholderText(
            "Chek raqami, masalan: 42"
        )
        self.receipt_number_edit.returnPressed.connect(self.search)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.search)

        search_button = PrimaryButton("Qidirish")
        search_button.clicked.connect(self.search)

        row.addWidget(QLabel("Chek raqami:"))
        row.addWidget(self.receipt_number_edit, 1)
        row.addWidget(QLabel("Sana:"))
        row.addWidget(self.date_edit)
        row.addWidget(search_button)

        return container

    def search(self):
        receipt_number = self.receipt_number_edit.text().strip()

        if receipt_number:
            self.search_by_number(receipt_number)
        else:
            self.search_by_date()

    def search_by_number(self, receipt_number):
        try:
            sale_id = int(receipt_number)
        except ValueError:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Chek raqami butun son bo'lishi kerak.",
            )
            return

        sale = SaleService.get_sale(sale_id)

        if sale is None:
            self.populate_results([])
            QMessageBox.warning(
                self,
                "Diqqat",
                "Bunday raqamli chek topilmadi.",
            )
            return

        self.populate_results([sale])
        self.results_table.selectRow(0)
        # Raqam bo'yicha qidiruv — bitta natija, shuning uchun
        # darhol yuklaymiz, kassir yana bir marta bosishi shart emas.
        self.load_sale(sale)

    def search_by_date(self):
        selected_date = self.date_edit.date().toPython()
        sales = SaleService.get_sales_by_date(selected_date)
        self.populate_results(sales)

    def populate_results(self, sales):
        self._results = {sale.id: sale for sale in sales}

        self.results_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            status_text, status_variant = resolve_sale_status(
                sale.status
            )

            id_item = QTableWidgetItem(str(sale.id))
            id_item.setData(Qt.UserRole, sale.id)

            self.results_table.setItem(row, 0, id_item)
            self.results_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    sale.created_at.strftime("%d.%m.%Y %H:%M")
                ),
            )
            self.results_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    f"{format_money(sale.total_amount)} so'm"
                ),
            )
            self.results_table.setCellWidget(
                row, 3, badge_cell(status_text, status_variant)
            )

    def on_result_selected(self, row, column):
        item = self.results_table.item(row, 0)

        if item is None:
            return

        sale = self._results.get(item.data(Qt.UserRole))

        if sale is None:
            return

        self.load_sale(sale)

    def load_sale(self, sale):
        self._sale = sale
        self._row_inputs = {}
        self._sale_items = SaleService.get_sale_items(sale.id)

        status_text, _ = resolve_sale_status(sale.status)

        self.sale_info_label.setText(
            f"Chek #{sale.id} — "
            f"{sale.created_at.strftime('%d.%m.%Y %H:%M')} — "
            f"{format_money(sale.total_amount)} so'm — {status_text}"
        )

        self.items_table.setRowCount(len(self._sale_items))

        for row, sale_item in enumerate(self._sale_items):
            remaining = max(
                0, sale_item.quantity - sale_item.returned_quantity
            )

            self.items_table.setItem(
                row, 0, QTableWidgetItem(sale_item.product_name)
            )
            self.items_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    f"{format_money(sale_item.price)} so'm"
                ),
            )
            self.items_table.setItem(
                row,
                2,
                QTableWidgetItem(format_quantity(sale_item.quantity)),
            )
            self.items_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    format_quantity(sale_item.returned_quantity)
                ),
            )
            self.items_table.setItem(
                row, 4, QTableWidgetItem(format_quantity(remaining))
            )

            spinbox = self._build_quantity_spinbox(
                sale_item, remaining
            )
            self.items_table.setCellWidget(row, 5, spinbox)

            self._row_inputs[sale_item.id] = (spinbox, sale_item)

        self.update_total()
        self.confirm_button.setEnabled(sale.status != "refunded")

    def _build_quantity_spinbox(self, sale_item, remaining):
        product = ProductService.get_product(sale_item.product_id)
        unit = (
            (product.unit or "").strip().lower() if product else ""
        )

        spinbox = QDoubleSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(remaining)

        if unit in {"kg", "кг"}:
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.1)
        else:
            spinbox.setDecimals(0)
            spinbox.setSingleStep(1)

        spinbox.setValue(0)
        spinbox.setEnabled(remaining > 0)
        spinbox.valueChanged.connect(self.update_total)

        return spinbox

    def fill_max_quantities(self):
        for spinbox, sale_item in self._row_inputs.values():
            remaining = max(
                0, sale_item.quantity - sale_item.returned_quantity
            )
            spinbox.setValue(remaining)

    def update_total(self):
        total = 0

        for spinbox, sale_item in self._row_inputs.values():
            total += spinbox.value() * sale_item.price

        self.total_refund_label.setText(
            f"Qaytariladigan summa: {format_money(total)} so'm"
        )

    def confirm_refund(self):
        if self._sale is None:
            return

        items = [
            {"sale_item_id": sale_item_id, "quantity": spinbox.value()}
            for sale_item_id, (spinbox, _) in self._row_inputs.items()
            if spinbox.value() > 0
        ]

        if not items:
            QMessageBox.warning(
                self,
                "Diqqat",
                "Qaytariladigan mahsulot miqdorini kiriting.",
            )
            return

        current_user = get_current_user()
        cashier_name = (
            current_user.full_name if current_user else None
        )
        cashier_user_id = current_user.id if current_user else None

        try:
            refund = RefundService.create_refund(
                self._sale.id,
                items,
                cashier_name=cashier_name,
                cashier_user_id=cashier_user_id,
            )

        except ValueError as error:
            QMessageBox.warning(self, "Diqqat", str(error))
            return

        except Exception:
            QMessageBox.critical(
                self,
                "Xatolik",
                "Qaytarishni saqlashda xatolik yuz berdi.",
            )
            return

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            f"Qaytarildi: {format_money(refund.total_amount)} so'm",
        )

        updated_sale = SaleService.get_sale(self._sale.id)
        self.load_sale(updated_sale)
        self.refundCompleted.emit()
