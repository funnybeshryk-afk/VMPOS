from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
)

from app.services.receipt_service import ReceiptPrintError, ReceiptService
from app.widgets.secondary_button import SecondaryButton
from app.widgets.success_button import SuccessButton
from app.i18n import tr


class ReceiptPreviewDialog(QDialog):
    """Chekning ekrandagi ko'rinishi + chop etish yoki PDF'ga saqlash.
    FISKAL chek emas (chekda shunday yozilgan)."""

    def __init__(self, receipt, parent=None):
        super().__init__(parent)

        self._receipt = receipt

        self.setWindowTitle(tr("Chek"))
        self.resize(520, 720)

        image = ReceiptService.render(receipt, antialias=True)

        label = QLabel()
        label.setPixmap(QPixmap.fromImage(image))
        label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        label.setStyleSheet("background: #ffffff;")

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)

        self.print_button = SuccessButton(tr("Chop etish"), large=True)
        self.print_button.clicked.connect(self.print_receipt)

        self.pdf_button = SecondaryButton(tr("PDF saqlash"), large=True)
        self.pdf_button.clicked.connect(self.save_pdf)

        close_button = SecondaryButton(tr("Yopish"), large=True)
        close_button.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(close_button, 1)
        buttons.addWidget(self.pdf_button, 1)
        buttons.addWidget(self.print_button, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(scroll, 1)
        layout.addLayout(buttons)

    def print_receipt(self):
        try:
            ReceiptService.print_receipt(self._receipt)
        except ReceiptPrintError as error:
            QMessageBox.warning(self, tr("Chek chop etilmadi"), str(error))

    def save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Chekni PDF sifatida saqlash"), "chek.pdf", tr("PDF fayllar (*.pdf)")
        )

        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            ReceiptService.print_receipt(self._receipt, pdf_path=path)
        except ReceiptPrintError as error:
            QMessageBox.warning(self, tr("PDF saqlanmadi"), str(error))
