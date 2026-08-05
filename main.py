import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow

from app.database.database import engine
from app.database.base import Base

import app.models.product

def main():
    app = QApplication(sys.argv)
    with open("assets/styles/style.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    Base.metadata.create_all(bind=engine)
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()