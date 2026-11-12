"""Fayl logi va kutilmagan xatolarni ushlash.

Kassada xato bo'lganda kassir "nimadir buzildi" deydi, xolos. Log
fayli (ma'lumotlar papkasidagi logs/vmpos.log) bo'lsa — nima
bo'lganini keyin ko'rish mumkin. Fayl aylanadi (1 MB x 5), shuning
uchun diskni to'ldirib yubormaydi.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from app.utils.paths import get_logs_dir

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

_showing_error_dialog = False


def get_log_path():
    return get_logs_dir() / "vmpos.log"


def setup_logging():
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Qayta chaqirilsa (testlar) handler takrorlanmasin.
    for handler in root.handlers:
        if getattr(handler, "_vmpos_file_handler", False):
            return

    handler = RotatingFileHandler(
        get_log_path(),
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler._vmpos_file_handler = True
    root.addHandler(handler)

    sys.excepthook = _handle_uncaught
    threading.excepthook = _handle_thread_uncaught


def _handle_uncaught(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger("uncaught").critical(
        "Kutilmagan xato", exc_info=(exc_type, exc_value, exc_traceback)
    )
    _show_error_dialog()


def _handle_thread_uncaught(args):
    _handle_uncaught(args.exc_type, args.exc_value, args.exc_traceback)


def _show_error_dialog():
    """Qt slotlaridagi xatolar ham shu yerga tushadi (PySide6 ularni
    sys.excepthook'ga uzatadi). Dastur yopilmaydi — kassir ishlashda
    davom etishi mumkin, lekin xato yo'qolib ketmaydi."""

    global _showing_error_dialog

    if _showing_error_dialog:
        return

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except Exception:
        return

    if QApplication.instance() is None:
        return

    _showing_error_dialog = True

    try:
        QMessageBox.critical(
            None,
            "Xatolik",
            "Dasturda kutilmagan xatolik yuz berdi.\n\n"
            "Ma'lumotlar saqlangan. Agar xato takrorlansa, dasturni "
            "qayta oching va quyidagi log faylini yuboring:\n"
            f"{get_log_path()}",
        )
    finally:
        _showing_error_dialog = False
