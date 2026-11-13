import os
import sys
import tempfile
from pathlib import Path

# Ma'lumotlar papkasi app.* import qilinishidan OLDIN vaqtinchalik
# papkaga yo'naltiriladi — testlar hech qachon haqiqiy bazaga tegmaydi.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="vmpos_test_")
os.environ["VMPOS_DATA_DIR"] = _TEST_DATA_DIR
# Qt oynalari ekransiz (CI/Linux) ishlashi uchun.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil  # noqa: E402

import pytest  # noqa: E402

from app.database.database import DATABASE_PATH, engine  # noqa: E402
from app.utils.paths import get_backup_dir  # noqa: E402


@pytest.fixture(autouse=True)
def clean_data_dir():
    def wipe():
        engine.dispose()
        DATABASE_PATH.unlink(missing_ok=True)
        shutil.rmtree(get_backup_dir(), ignore_errors=True)

    wipe()
    yield
    wipe()


@pytest.fixture(scope="session")
def qapp():
    import gc

    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    yield app

    # Toza yakun: testlar ochib qoldirgan oynalar/taymerlar/animatsiyalar
    # QApplication yo'q qilinayotganda tirik qolsa, Qt interpreter yopilishida
    # noto'g'ri tartibda o'chiradi va jarayon "Bus error"/exit code != 0 bilan
    # tugaydi (testlar o'tgan bo'lsa ham CI qizil bo'ladi).
    app.closeAllWindows()

    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()

    app.processEvents()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    gc.collect()


@pytest.fixture(autouse=True)
def animations_off_by_default():
    """Mantiq testlari animatsiyasiz (darhol yakuniy holat) ishlaydi;
    animatsiya testlari ularni o'zlari yoqadi (tests/test_motion.py)."""

    from app.utils import motion

    previous = motion.is_enabled()
    motion.set_enabled(False)
    yield
    motion.set_enabled(previous)
