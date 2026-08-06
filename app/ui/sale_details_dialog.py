from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.sale_service import SaleService


class SaleDetailsDialog(QDialog):
    def __init__(self, sale, parent=None):
        super().__init__(parent)

        self.sale = sale

        self.setWindowTitle(f"Chek #{sale.id}")
        self.resize(600, 450)

        main_layout = QVBoxLayout(self)

        title = QLabel(f"Chek #{sale.id}")
        title.setObjectName("pageTitle")

        if sale.status == "refunded":
            status_text = "Holat: Qaytarilgan"
        else:
            status_text = "Holat: Yakunlangan"

        self.status_label = QLabel(status_text)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels([
            "Mahsulot",
            "Narxi",
            "Soni",
            "Jami",
        ])

        self.items_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.items_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        total_label = QLabel(f"Jami: {sale.total_amount} so'm")

        self.refund_button = QPushButton("Chekni qaytarish")
        self.refund_button.clicked.connect(self.refund_sale)

        if sale.status == "refunded":
            self.refund_button.setDisabled(True)

        close_button = QPushButton("Yopish")
        close_button.clicked.connect(self.accept)

        main_layout.addWidget(title)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.items_table)
        main_layout.addWidget(total_label)
        main_layout.addWidget(self.refund_button)
        main_layout.addWidget(close_button)

        self.load_sale_items(sale.id)

    def load_sale_items(self, sale_id):
        sale_items = SaleService.get_sale_items(sale_id)

        self.items_table.setRowCount(len(sale_items))

        for row, sale_item in enumerate(sale_items):
            self.items_table.setItem(
                row,
                0,
                QTableWidgetItem(sale_item.product_name),
            )
            self.items_table.setItem(
                row,
                1,
                QTableWidgetItem(str(sale_item.price)),
            )
            self.items_table.setItem(
                row,
                2,
                QTableWidgetItem(str(sale_item.quantity)),
            )
            self.items_table.setItem(
                row,
                3,
                QTableWidgetItem(str(sale_item.line_total)),
            )

    def refund_sale(self):
        reply = QMessageBox.question(
            self,
            "Tasdiqlash",
            "Bu chekni qaytarmoqchimisiz?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            SaleService.refund_sale(self.sale.id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Diqqat",
                str(error),
            )
            return

        self.sale.status = "refunded"

        QMessageBox.information(
            self,
            "Muvaffaqiyatli",
            "Chek qaytarildi. Mahsulotlar qoldiqqa qaytdi.",
        )

        self.accept()