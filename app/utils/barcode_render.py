import barcode


def get_barcode_modules(code):
    """Code128 shtrix-kod uchun modul ketma-ketligi — '1' (chiziq)
    va '0' (bo'shliq) belgilaridan iborat satr, to'g'ridan-to'g'ri
    QPainter bilan chizish uchun.

    Avval python-barcode'ning SVGWriter'i orqali SVG hosil qilib,
    uni QSvgRenderer bilan chizishga urinilgan edi. Lekin QtSvg
    millimetr birlikli <rect> elementlarining x/width koordinatalarini
    noto'g'ri o'qiydi — barcha chiziqlar chap tomonga siqilib,
    bir-birining ustiga tushib, yagona qora blokka aylanib qoladi
    (vizual tekshiruv orqali aniqlangan haqiqiy xato, taxmin emas).
    Shu sabab shtrix-kod endi oraliq SVG formatisiz, modul-modul
    to'g'ridan-to'g'ri chiziladi (label_printing.py).

    Code128 tanlangan — ixtiyoriy uzunlik/belgilar to'plamini
    (mahsulot shtrix-kodi raqam yoki matn bo'lishidan qat'iy nazar)
    xatosiz kodlay oladi, EAN13 kabi qat'iy 12-13 xonali raqam talab
    qilmaydi.
    """

    code = (code or "").strip()

    if not code:
        return None

    try:
        barcode_class = barcode.get_barcode_class("code128")
        modules = barcode_class(code).build()[0]
    except Exception:
        return None

    return modules
