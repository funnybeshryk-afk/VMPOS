from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
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
from app.utils.icons import load_icon
from app.utils.paths import get_bundle_base_dir
from app.widgets.app_status_bar import AppStatusBar
from app.widgets.sidebar_menu import SidebarMenu

_SIDEBAR_PADDING = 16

# (matn kaliti -> Feather ikonka nomi). Aniq muqobili yo'q joylarda
# eng yaqin ma'nodagi ikonka tanlangan: Ombor — "archive" (ombor
# qutisi), Moliya — "layers" (Sotuv'dagi naqd to'lov tugmasidagi
# bilan bir xil — "pul uyumi", valyuta belgisiz), Foydalanuvchilar —
# "user-check" (xodimni tasdiqlash/boshqarish).
_MENU_ICONS = {
    "sale": "shopping-cart",
    "products": "package",
    "warehouse": "archive",
    "reports": "bar-chart-2",
    "customers": "users",
    "suppliers": "truck",
    "finance": "layers",
    "users": "user-check",
    "settings": "settings",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VMPOS v1.0.0")
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

        # Sidebar — logo, menyu va profil bitta ustunda (#sidebar).
        # Har uch bo'lim ham bir xil _SIDEBAR_PADDING'dan boshlanadi,
        # shu sabab ular bitta tekis chetdagi yagona guruh sifatida
        # ko'rinadi.
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_layout.addWidget(self._build_logo_row())

        self.sidebar_menu = SidebarMenu()
        self.sidebar_menu.itemSelected.connect(self.change_page)

        sidebar_layout.addWidget(self.sidebar_menu, 1)
        sidebar_layout.addWidget(self._build_user_panel())

        self.workspace = QStackedWidget()

        self.sale_page = SalePage()
        self.sale_page.shift_panel.openMoliyaRequested.connect(
            self.go_to_finance_page
        )
        self.products_page = ProductsPage()
        self.warehouse_page = WarehousePage()
        self.reports_page = ReportsPage()
        self.customers_page = CustomersPage()
        self.suppliers_page = SuppliersPage()
        self.finance_page = FinancePage()
        self.users_page = UsersPage()
        self.settings_page = SettingsPage()

        # Kassirga faqat o'z ishi uchun kerakli ikkita bet ochiq —
        # Sotuv (chek yozish) va Moliya (o'z smenasini boshqarish),
        # qolgani — orqa ofis ishi — faqat Administratorga.
        self._pages_by_key = {
            "sale": (self.sale_page, None),
            "products": (self.products_page, {ROLE_ADMIN}),
            "warehouse": (self.warehouse_page, {ROLE_ADMIN}),
            "reports": (self.reports_page, {ROLE_ADMIN}),
            "customers": (self.customers_page, {ROLE_ADMIN}),
            "suppliers": (self.suppliers_page, {ROLE_ADMIN}),
            "finance": (self.finance_page, None),
            "users": (self.users_page, {ROLE_ADMIN}),
            "settings": (self.settings_page, {ROLE_ADMIN}),
        }

        self._menu_groups = [
            ("Asosiy", ["sale", "products", "warehouse", "reports"]),
            ("Aloqalar", ["customers", "suppliers"]),
            ("Boshqaruv", ["finance", "users", "settings"]),
        ]

        for page, _roles in self._pages_by_key.values():
            self.workspace.addWidget(page)

        content_layout.addWidget(sidebar)
        content_layout.addWidget(self.workspace)

        self.status_bar = AppStatusBar()

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_bar)

    def _build_logo_row(self):
        logo_row = QWidget()
        logo_row.setObjectName("sidebarLogo")

        logo_row_layout = QHBoxLayout(logo_row)
        # O'ng chekka boshqalarga qaraganda torroq (8px) — 220px
        # sidebar'ga kattalashtirilgan ikonka (67px) + "Vodiy Market"
        # matni (18px qalin shriftda ~114px) sig'ishi uchun, aks
        # holda matn o'ngdan kesilib qolar edi. Chap chekka esa
        # _SIDEBAR_PADDING bilan menyu bilan bir xil — tekislik
        # buzilmaydi.
        logo_row_layout.setContentsMargins(
            _SIDEBAR_PADDING, 18, 8, 18
        )
        logo_row_layout.setSpacing(8)

        # To'liq logotipda "Vodiy Market" yozuvi ham bor — bu yerda
        # faqat belgi (yuqori doira+savat+barglar qismi) kesib
        # olinadi, nomi esa alohida oddiy matn sifatida yoniga
        # qo'yiladi, aks holda nom ikki marta takrorlanib qolardi.
        # Kesish to'rtburchagi rasmning haqiqiy piksel chegaralarini
        # o'lchab aniqlangan (belgi x:208-1050, y:99-814) — avvalgi
        # qiymat (150,0,960,800) pastki barglarning uchini kesib
        # tashlar edi, shu sabab ikonka siqilgan/obrezan ko'rinardi.
        # Balandlik 56px'ga oshirilgan (36px avvalgi urinishda hali
        # ham kichik ko'rinar edi) — kenglik nisbatiga ko'ra ~67px.
        logo_path = get_bundle_base_dir() / "assets" / "logo.png"

        icon_label = QLabel()
        icon_label.setPixmap(
            QPixmap(str(logo_path))
            .copy(180, 80, 900, 750)
            .scaledToHeight(56, Qt.SmoothTransformation)
        )

        name_label = QLabel("Vodiy Market")
        name_label.setObjectName("sidebarLogoText")

        logo_row_layout.addWidget(icon_label)
        logo_row_layout.addWidget(name_label)
        logo_row_layout.addStretch()

        return logo_row

    def _build_user_panel(self):
        # Ilovada parol talab qilmaydigan yengil "hozir kim
        # ishlayapti" ko'rsatkichi — menyuni rolga qarab moslashtirish
        # va Moliya'da kassirni oldindan belgilash uchun ishlatiladi.
        user_panel = QWidget()
        user_panel.setObjectName("sidebarUserPanel")

        user_panel_layout = QHBoxLayout(user_panel)
        user_panel_layout.setContentsMargins(
            _SIDEBAR_PADDING, 12, _SIDEBAR_PADDING, 12
        )
        user_panel_layout.setSpacing(10)

        self.user_avatar_label = QLabel()
        self.user_avatar_label.setObjectName("sidebarUserAvatar")
        self.user_avatar_label.setFixedSize(36, 36)
        self.user_avatar_label.setAlignment(Qt.AlignCenter)

        user_text_layout = QVBoxLayout()
        user_text_layout.setSpacing(0)

        self.current_user_name_label = QLabel()
        self.current_user_name_label.setObjectName("sidebarUserName")

        self.current_user_role_label = QLabel()
        self.current_user_role_label.setObjectName("mutedText")

        user_text_layout.addWidget(self.current_user_name_label)
        user_text_layout.addWidget(self.current_user_role_label)

        self.switch_user_button = QPushButton()
        self.switch_user_button.setObjectName(
            "sidebarSwitchUserButton"
        )
        self.switch_user_button.setIcon(
            load_icon("log-out", color="#57534e", size=18)
        )
        self.switch_user_button.setIconSize(QSize(18, 18))
        self.switch_user_button.setFixedSize(32, 32)
        self.switch_user_button.setCursor(Qt.PointingHandCursor)
        self.switch_user_button.setToolTip("Almashtirish")
        self.switch_user_button.clicked.connect(
            self.switch_active_user
        )

        user_panel_layout.addWidget(self.user_avatar_label)
        user_panel_layout.addLayout(user_text_layout, 1)
        user_panel_layout.addWidget(self.switch_user_button)

        return user_panel

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

        groups = []
        visible_keys = []

        for group_title, keys in self._menu_groups:
            entries = []

            for key in keys:
                _page, roles = self._pages_by_key[key]

                if (
                    roles is not None
                    and current_user is not None
                    and current_role not in roles
                ):
                    continue

                entries.append((key, TEXT[key], _MENU_ICONS[key]))
                visible_keys.append(key)

            groups.append((group_title, entries))

        self.sidebar_menu.set_groups(groups)
        self._visible_keys = visible_keys

        if current_user is None:
            self.user_avatar_label.setText("")
            self.current_user_name_label.setText(
                "Foydalanuvchi tanlanmagan"
            )
            self.current_user_role_label.setText("")
        else:
            self.user_avatar_label.setText(
                current_user.full_name[:1].upper()
            )
            self.current_user_name_label.setText(
                current_user.full_name
            )
            self.current_user_role_label.setText(
                ROLE_LABELS.get(
                    current_user.role, current_user.role
                )
            )

        if not visible_keys:
            return

        # Mahsulotlar — sahifa ochilganda ko'rsatiladigan odatiy bet
        # (Kassir uchun ko'rinmasa, ro'yxatdagi birinchi bet olinadi).
        default_key = (
            "products"
            if "products" in visible_keys
            else visible_keys[0]
        )
        self.sidebar_menu.select(default_key)

    def go_to_finance_page(self):
        # Moliya barcha rollarga ochiq (_pages_by_key'da roles=None),
        # shuning uchun u har doim joriy ko'rinadigan menyuda bo'ladi.
        self.sidebar_menu.select("finance")

    def change_page(self, key):
        if key not in self._pages_by_key:
            return

        page, _roles = self._pages_by_key[key]

        if page is self.sale_page:
            self.sale_page.load_products()

        self.workspace.setCurrentWidget(page)
