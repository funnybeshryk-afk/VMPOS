"""Interfeys tili (uz — asosiy, ru — ikkinchi).

Kalit — o'zbekcha asl matn: kodda tr("Sotuv") deb yoziladi, rus tilida
app/resources/ru.py lug'atidan tarjima qilinadi. Tarjima topilmasa —
asl o'zbekcha matn ko'rinadi (dastur hech qachon bo'sh matn ko'rsatmaydi).
f-satrlar o'rniga shablon ishlatiladi: tr("Jami: {0} so'm").format(x).

Til dastur ishga tushganda BIR marta o'rnatiladi (oynalar yaratilishidan
oldin); o'zgartirish — qayta ishga tushirgandan keyin kuchga kiradi.
"""

SUPPORTED = ("uz", "ru")
DEFAULT = "uz"

_language = DEFAULT
_ru = None


def get_language():
    return _language


def set_language(code):
    global _language
    _language = code if code in SUPPORTED else DEFAULT


def _ru_table():
    global _ru
    if _ru is None:
        from app.resources.ru import RU

        _ru = RU

    return _ru


def tr(text):
    if _language == "ru":
        return _ru_table().get(text, text)

    return text


LANGUAGE_SETTING_KEY = "language"


def load_saved_language():
    """Sozlamalardan saqlangan tilni o'qib, o'rnatadi. Baza tayyor
    bo'lgandan keyin, oynalar yaratilishidan OLDIN chaqiriladi."""

    from app.services.settings_service import SettingsService

    try:
        code = SettingsService.get_setting(LANGUAGE_SETTING_KEY, DEFAULT)
    except Exception:
        code = DEFAULT

    set_language(code)

    return get_language()


def save_language(code):
    from app.services.settings_service import SettingsService

    if code not in SUPPORTED:
        raise ValueError(code)

    SettingsService.save_setting(LANGUAGE_SETTING_KEY, code)


def install_qt_translations(app):
    """Qt'ning standart matnlari (Yes/No, kalendar, fayl oynasi...) ham
    tanlangan tilda chiqishi uchun. Fayl topilmasa — jimgina o'tkazib
    yuboriladi (inglizcha qoladi)."""

    if _language != "ru":
        return None

    from PySide6.QtCore import QLibraryInfo, QTranslator

    translator = QTranslator(app)
    path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)

    if translator.load("qtbase_ru", path):
        app.installTranslator(translator)

        return translator

    return None
