from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QToolButton,
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
from app.version import APP_VERSION
from app.widgets.app_status_bar import AppStatusBar
from app.widgets.sidebar_menu import SidebarMenu

# (matn kaliti -> Feather ikonka nomi). Aniq muqobili yo'q joylarda
# eng yaqin ma'nodagi ikonka tanlangan: Ombor — "archive" (ombor
# qutisi), Moliya — "layers" (Sotuv'dagi naqd to'lov tugmasidagi
# bilan bir xil — "pul uyumi", valyuta belgisiz), Foydalanuvchilar —
# "user-check" (xodimni tasdiqlash/boshqarish).
# Rels kengligi 96 px — uzun nomlar sig'maydi: rels yorlig'i qisqa,
# to'liq nom (TEXT) tooltip sifatida ko'rsatiladi.
_RAIL_LABELS = {
    "sale": "Sotuv",
    "products": "Mahsulot",
    "warehouse": "Ombor",
    "reports": "Hisobot",
    "customers": "Mijoz",
    "suppliers": "Ta'minot",
    "finance": "Moliya",
    "users": "Xodimlar",
    "settings": "Sozlama",
}

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

        self.setWindowTitle(f"VMPOS v{APP_VERSION}")
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

        # Chap "rels" — logo, menyu va profil bitta ustunda (#sidebar).
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(96)

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
        # Rels ichida logo — faqat belgi (savat+barglar), oq "badge"
        # ichida (brend qoidasi: logotip rangli fonda emas, oq/neytral
        # fonda turadi). To'liq nom "Vodiy Market" rels kengligiga
        # sig'maydi va tooltip'da.
        #
        # Kesish to'rtburchagi rasmning haqiqiy piksel chegaralarini
        # o'lchab aniqlangan (belgi x:208-1050, y:99-814); (180,80,900,750)
        # pastki barglarni kesmaydi.
        logo_row = QWidget()
        logo_row.setObjectName("sidebarLogo")

        logo_row_layout = QVBoxLayout(logo_row)
        logo_row_layout.setContentsMargins(0, 16, 0, 8)

        logo_path = get_bundle_base_dir() / "assets" / "logo.png"

        icon_label = QLabel()
        icon_label.setObjectName("railLogo")
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setToolTip("Vodiy Market")
        icon_label.setPixmap(
            QPixmap(str(logo_path))
            .copy(180, 80, 900, 750)
            .scaled(
                52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

        logo_row_layout.addWidget(icon_label, 0, Qt.AlignHCenter)

        return logo_row

    def _build_user_panel(self):
        # Rels pastidagi doira — joriy xodim bosh harfi. Bosilsa
        # xodim almashtiriladi; ism va rol tooltip'da. Ilovada parol
        # talab qilmaydigan yengil "hozir kim ishlayapti" ko'rsatkichi:
        # menyuni rolga qarab moslashtirish va Moliya'da kassirni
        # oldindan belgilash uchun ishlatiladi.
        user_panel = QWidget()
        user_panel.setObjectName("sidebarUserPanel")

        user_panel_layout = QVBoxLayout(user_panel)
        user_panel_layout.setContentsMargins(0, 8, 0, 16)

        self.switch_user_button = QToolButton()
        self.switch_user_button.setObjectName("railAvatar")
        self.switch_user_button.setFixedSize(48, 48)
        self.switch_user_button.setCursor(Qt.PointingHandCursor)
        self.switch_user_button.clicked.connect(
            self.switch_active_user
        )

        user_panel_layout.addWidget(
            self.switch_user_button, 0, Qt.AlignHCenter
        )

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

                entries.append(
                    (
                        key,
                        _RAIL_LABELS[key],
                        _MENU_ICONS[key],
                        TEXT[key],
                    )
                )
                visible_keys.append(key)

            groups.append((group_title, entries))

        self.sidebar_menu.set_groups(groups)
        self._visible_keys = visible_keys

        if current_user is None:
            self.switch_user_button.setText("")
            self.switch_user_button.setIcon(
                load_icon("user", color="#ffffff", size=22)
            )
            self.switch_user_button.setToolTip(
                "Foydalanuvchi tanlanmagan — bosing"
            )
        else:
            role_text = ROLE_LABELS.get(
                current_user.role, current_user.role
            )

            self.switch_user_button.setIcon(QIcon())
            self.switch_user_button.setText(
                current_user.full_name[:1].upper()
            )
            self.switch_user_button.setToolTip(
                f"{current_user.full_name} · {role_text}\n"
                "Almashtirish uchun bosing"
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
