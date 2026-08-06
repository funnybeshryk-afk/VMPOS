import sys

from PySide6.QtWidgets import QApplication

from app.database.base import Base
from app.database.database import engine
from app.database.migrations import apply_migrations
from app.ui.main_window import MainWindow

import app.models.customer
import app.models.debt_payment
import app.models.product
import app.models.sale
import app.models.stock_receipt
import app.models.supplier


def main():
    app = QApplication(sys.argv)

    with open("assets/styles/style.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    Base.metadata.create_all(bind=engine)
    apply_migrations()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()