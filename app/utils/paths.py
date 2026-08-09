import sys
from pathlib import Path


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
