import os
import sys
from pathlib import Path

DATA_DIR_NAME = "VMPOS"
DATA_DIR_ENV = "VMPOS_DATA_DIR"


def get_app_base_dir():
    """Doimiy foydalanuvchi ma'lumotlari (baza, zaxira nusxalar,
    mahsulot rasmlari) qayerda saqlanishi kerakligini aniqlaydi.

    PyInstaller bilan yig'ilgan .exe holida (`sys.frozen`) — exe
    joylashgan papka qaytariladi. Build paketining o'zi (--onefile
    rejimida ishga tushirilganda vaqtinchalik ochiladigan papka,
    --onedir'da esa qayta yig'ilganda almashtirib qo'yiladigan
    papka) qayta yig'ilganda yo'qolib/almashtirilib turadi —
    foydalanuvchi ma'lumotlari esa shu bilan birga yo'qolib
    qolmasligi kerak, shuning uchun ular EXE bilan bir qatorda,
    undan tashqarida saqlanadi.

    Oddiy `python main.py` bilan ishga tushirilganda — loyihaning
    ildiz papkasi qaytariladi. Bu joriy ish papkasi (CWD) qanday
    bo'lishidan qat'iy nazar barqaror, chunki bu fayl loyiha
    tuzilishida doim bir xil joyda turadi (app/utils/paths.py —
    ildizdan uch daraja pastda).
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent.parent


def get_bundle_base_dir():
    """O'qish uchun mo'ljallangan build vaqtidagi resurslar (uslub
    fayli style.qss, logotip, ikonkalar) qayerda joylashganini
    aniqlaydi — get_app_base_dir()'dan farqli maqsad bilan.

    PyInstaller --add-data orqali qo'shilgan fayllar CWD'ga emas,
    sys._MEIPASS ko'rsatgan papkaga chiqariladi (--onefile'da har
    ishga tushganda yaratiladigan vaqtinchalik papka, --onedir'da
    esa EXE bilan bir xil papka). Bu YOZISH uchun emas — faqat
    O'QISH uchun: build paketi qayta yig'ilganda bu joy har safar
    to'liq yangilanadi, shuning uchun foydalanuvchi ma'lumotlari
    (baza, zaxira, rasmlar) bu yerda emas, get_app_base_dir()da
    saqlanadi.

    Oddiy `python main.py` bilan ishga tushirilganda — loyihaning
    ildiz papkasi (get_app_base_dir() bilan bir xil).
    """

    bundle_dir = getattr(sys, "_MEIPASS", None)

    if bundle_dir:
        return Path(bundle_dir)

    return Path(__file__).resolve().parent.parent.parent


def get_data_dir():
    """Foydalanuvchi ma'lumotlari (baza, zaxiralar, rasmlar, loglar)
    saqlanadigan papka — DASTUR PAPKASIDAN ALOHIDA.

    Sabab: dasturni yangilashda (exe'ni almashtirish, qayta o'rnatish)
    dastur papkasi butunlay almashtirilishi yoki o'chirilishi mumkin,
    "Program Files" ichida esa yozishga ruxsat ham yo'q. Ma'lumotlar
    esa hech qachon dastur fayllari bilan birga turmasligi kerak.

    Tartib:
      1. VMPOS_DATA_DIR muhit o'zgaruvchisi (testlar, qo'lda sozlash);
      2. .exe rejimida — %LOCALAPPDATA%\\VMPOS;
      3. oddiy `python main.py` — loyiha ildizi (avvalgidek, ishlab
         chiqish uchun hech narsa o'zgarmaydi).
    """

    override = os.environ.get(DATA_DIR_ENV)

    if override:
        data_dir = Path(override)
    elif getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA")

        if base:
            data_dir = Path(base) / DATA_DIR_NAME
        else:
            data_dir = Path.home() / ".vmpos"
    else:
        data_dir = get_app_base_dir()

    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def get_database_path():
    return get_data_dir() / "vmpos.db"


def get_backup_dir():
    return get_data_dir() / "backups"


def get_logs_dir():
    return get_data_dir() / "logs"


def get_product_images_dir():
    return get_data_dir() / "assets" / "products"


def to_data_relative(path):
    """Fayl yo'lini ma'lumotlar papkasiga NISBIY ko'rinishda (har doim
    "/" bilan) qaytaradi — bazada shu saqlanadi, shuning uchun papka
    ko'chirilsa ham rasmlar yo'qolmaydi."""

    path = Path(path)

    try:
        return path.relative_to(get_data_dir()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_data_path(path):
    """Bazadagi yo'lni haqiqiy faylga aylantiradi: nisbiy bo'lsa —
    ma'lumotlar papkasiga nisbatan, eski (mutlaq) yozuvlar esa o'zgarishsiz
    ishlayveradi."""

    if not path:
        return None

    path = Path(path)

    if path.is_absolute():
        return path

    return get_data_dir() / path
