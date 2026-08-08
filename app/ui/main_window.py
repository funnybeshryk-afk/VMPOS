from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.user import ROLE_ADMIN, ROLE_LABELS
from app.resources.language import TEXT
from app.services.user_service import UserService
from app.state.session import get_current_user, set_current_user
from app.ui.customers_page import CustomersPage
from app.ui.finance_page import FinancePage
from app.ui.products_page import ProductsPage
from app.ui.reports_page import ReportsPage
from app.ui.sale_page import SalePage
from app.ui.settings_page import SettingsPage
from app.ui.suppliers_page import SuppliersPage
from app.ui.user_picker_dialog import UserPickerDialog
from app.ui.users_page import UsersPage
from app.ui.warehouse_page import WarehousePage
from app.widgets.app_status_bar import AppStatusBar
from app.widgets.ghost_button import GhostButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VMPOS")
        self.setWindowIcon(QIcon("assets/logo.png"))
        self.resize(1200, 700)

        self._build_ui()
        self._choose_active_user()
        self.rebuild_menu()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar — logo va menyuni bitta ustunga birlashtiradigan
        # konteyner. Ranglash (fon, o'ng chegara) shu konteynerda
        # #sidebar orqali beriladi — logo va ro'yxat bir xil oq
        # panelning qismidek ko'rinishi uchun.
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_label = QLabel()
        logo_label.setObjectName("sidebarLogo")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setPixmap(
            QPixmap("assets/logo.png").scaledToWidth(
                140,
                Qt.SmoothTransformation,
            )
        )

        self.menu = QListWidget()
        self.menu.currentRowChanged.connect(self.change_page)

        # Ilovada parol talab qilmaydigan yengil "hozir kim
        # ishlayapti" ko'rsatkichi — menyuni rolga qarab moslashtirish
        # va Moliya'da kassirni oldindan belgilash uchun ishlatiladi.
        user_panel = QWidget()

        user_panel_layout = QVBoxLayout(user_panel)
        user_panel_layout.setContentsMargins(16, 12, 16, 16)
        user_panel_layout.setSpacing(4)

        self.current_user_label = QLabel()
        self.current_user_label.setObjectName("mutedText")
        self.current_user_label.setWordWrap(True)

        self.switch_user_button = GhostButton("Almashtirish")
        self.switch_user_button.clicked.connect(
            self.switch_active_user
        )

        user_panel_layout.addWidget(self.current_user_label)
        user_panel_layout.addWidget(self.switch_user_button)

        self.workspace = QStackedWidget()

        self.sale_page = SalePage()
        self.products_page = ProductsPage()
        self.warehouse_page = WarehousePage()
        self.reports_page = ReportsPage()
        self.customers_page = CustomersPage()
        self.suppliers_page = SuppliersPage()
        self.finance_page = FinancePage()
        self.users_page = UsersPage()
        self.settings_page = SettingsPage()

        # (matn kaliti, sahifa, faqat shu rollarga ko'rinadi — None
        # bo'lsa hammaga ko'rinadi). Kassirga faqat o'z ishi uchun
        # kerakli ikkita bet ochiq — Sotuv (chek yozish) va Moliya
        # (o'z smenasini boshqarish), qolgani — orqa ofis ishi —
        # faqat Administratorga.
        self._page_entries = [
            ("sale", self.sale_page, None),
            ("products", self.products_page, {ROLE_ADMIN}),
            ("warehouse", self.warehouse_page, {ROLE_ADMIN}),
            ("reports", self.reports_page, {ROLE_ADMIN}),
            ("customers", self.customers_page, {ROLE_ADMIN}),
            ("suppliers", self.suppliers_page, {ROLE_ADMIN}),
            ("finance", self.finance_page, None),
            ("users", self.users_page, {ROLE_ADMIN}),
            ("settings", self.settings_page, {ROLE_ADMIN}),
        ]

        for _text_key, page, _roles in self._page_entries:
            self.workspace.addWidget(page)

        self._visible_pages = []

        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addWidget(self.menu, 1)
        sidebar_layout.addWidget(user_panel)

        content_layout.addWidget(sidebar)
        content_layout.addWidget(self.workspace)

        self.status_bar = AppStatusBar()

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_bar)

    def _choose_active_user(self):
        users = UserService.get_all_users()

        # Hali birorta ham xodim qo'shilmagan — tanlanadigan hech kim
        # yo'q, shuning uchun to'liq (Administrator darajasidagi)
        # kirish bilan davom etiladi, aks holda "Foydalanuvchilar"
        # bo'limiga kirib birinchi xodimni qo'shishning iloji bo'lmay
        # qolardi.
        if not users:
            set_current_user(None)
            return

        dialog = UserPickerDialog(users, self)

        if dialog.exec():
            set_current_user(dialog.get_selected_user())

    def switch_active_user(self):
        users = UserService.get_all_users()

        if not users:
            set_current_user(None)
        else:
            dialog = UserPickerDialog(users, self)

            if dialog.exec():
                set_current_user(dialog.get_selected_user())

        self.rebuild_menu()

    def rebuild_menu(self):
        current_user = get_current_user()
        current_role = current_user.role if current_user else None

        visible_entries = []

        for text_key, page, roles in self._page_entries:
            if (
                roles is not None
                and current_user is not None
                and current_role not in roles
            ):
                continue

            visible_entries.append((text_key, page))

        self.menu.blockSignals(True)
        self.menu.clear()

        for text_key, _page in visible_entries:
            self.menu.addItem(TEXT[text_key])

        self.menu.blockSignals(False)

        self._visible_pages = [
            page for _text_key, page in visible_entries
        ]

        if current_user is None:
            self.current_user_label.setText(
                "Foydalanuvchi tanlanmagan"
            )
        else:
            role_label = ROLE_LABELS.get(
                current_user.role, current_user.role
            )
            self.current_user_label.setText(
                f"{current_user.full_name}\n{role_label}"
            )

        if not self._visible_pages:
            return

        # Mahsulotlar — sahifa ochilganda ko'rsatiladigan odatiy bet
        # (Kassir uchun ko'rinmasa, ro'yxatdagi birinchi bet olinadi).
        default_row = 0

        for row, (text_key, _page) in enumerate(visible_entries):
            if text_key == "products":
                default_row = row
                break

        self.menu.setCurrentRow(default_row)

    def change_page(self, index):
        if index < 0 or index >= len(self._visible_pages):
            return

        page = self._visible_pages[index]

        if page is self.sale_page:
            self.sale_page.load_products()

        self.workspace.setCurrentWidget(page)
