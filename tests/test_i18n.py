import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app import i18n
from app.resources.ru import RU

ROOT = Path(__file__).resolve().parent.parent
_PLACEHOLDER = re.compile(r"\{\d+[^}]*\}")


def _code_keys():
    keys = set()

    for path in (ROOT / "app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "tr"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                keys.add(node.args[0].value)

    return keys


@pytest.fixture(autouse=True)
def _reset_language():
    yield
    i18n.set_language("uz")


def test_every_tr_key_has_russian_translation():
    missing = sorted(_code_keys() - set(RU))

    assert not missing, f"ru.py da tarjima yo'q ({len(missing)}): {missing[:10]}"


def test_no_stale_translations():
    stale = sorted(set(RU) - _code_keys())

    assert not stale, f"koddan yo'qolgan kalitlar: {stale[:10]}"


def test_placeholders_match():
    bad = [
        key
        for key, value in RU.items()
        if sorted(_PLACEHOLDER.findall(key)) != sorted(_PLACEHOLDER.findall(value))
    ]

    assert not bad, f"{{n}} joylari mos emas: {bad[:5]}"


def test_translations_are_russian():
    # Kirill harfi bo'lmagan tarjima — faqat brend/texnik matn (kalit bilan
    # bir xil) bo'lishi mumkin; aks holda tarjima unutilgan.
    bad = [
        k
        for k, v in RU.items()
        if not v.strip()
        or (not re.search("[а-яА-ЯёЁ]", v) and v != k)
        or (v == k and re.search(r"[a-z]['ʻ‘’]|\b(so'm|Qarz|Chek)\b", k))
    ]

    assert not bad, bad[:5]


def test_tr_switches_and_falls_back():
    i18n.set_language("uz")
    assert i18n.tr("Sotuv") == "Sotuv"

    i18n.set_language("ru")
    assert i18n.tr("Sotuv") == "Продажа"
    assert i18n.tr("bunaqa kalit yo'q") == "bunaqa kalit yo'q"

    i18n.set_language("xx")  # noma'lum til — standartga qaytadi
    assert i18n.get_language() == "uz"


def test_format_templates_keep_working_in_russian():
    i18n.set_language("ru")

    assert i18n.tr("Qaytarildi: {0} so'm").format("1 000") == "Возвращено: 1 000 сум"


_UZ_MARKER = re.compile(r"[a-zA-Z][o'ʻ‘g]['ʻ‘’]|\bso'm\b|\b(Sotuv|Mahsulot|Ombor|Hisobot|Mijoz|Nasiya|Naqd|Karta|Saqlash|Bekor)\b")

_SMOKE = r"""
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QAbstractButton
app = QApplication([])
from app.database.migrations import prepare_database
prepare_database()
from app import i18n
i18n.set_language("ru")           # interfeys modullari import qilinishidan OLDIN
from app.services.user_service import UserService
admin = UserService.create_user({"full_name": "Aziz Karimov", "role": "admin"})
from app.ui import main_window as mw
from app.ui import user_picker_dialog as upd
upd.UserPickerDialog.exec = lambda self: 1
upd.UserPickerDialog.get_selected_user = lambda self: admin
win = mw.MainWindow(); win.resize(1280, 760); win.show(); app.processEvents()
texts = set()
for key in ["sale", "products", "warehouse", "reports", "customers", "suppliers", "finance", "users", "settings"]:
    win.sidebar_menu.select(key); app.processEvents()
    for w in win.findChildren(QLabel) + win.findChildren(QAbstractButton):
        t = w.text()
        if t: texts.add(t)
        tip = w.toolTip()
        if tip: texts.add(tip)
print("\n".join(sorted(texts)))
"""


def test_russian_ui_has_no_uzbek_leftovers(tmp_path):
    env = dict(os.environ, VMPOS_DATA_DIR=str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", _SMOKE, str(ROOT)],
        capture_output=True, text=True, env=env, timeout=120,
    )

    assert result.returncode == 0, result.stderr[-800:]

    texts = [t for t in result.stdout.splitlines() if t.strip()]
    leftovers = [t for t in texts if _UZ_MARKER.search(t)]

    assert texts, "interfeysdan matn olinmadi"
    assert not leftovers, f"tarjima qilinmagan: {leftovers[:15]}"
