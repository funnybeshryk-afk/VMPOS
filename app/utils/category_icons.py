# Feather'da oziq-ovqatga xos ikonkalar yo'q (apple/egg kabi shakllar
# umuman mavjud emas) — shuning uchun har bir kategoriya uchun eng
# yaqin mazmundagi umumiy ikonka tanlangan, aniq surat emas. CategoryBar
# (Sotuv filtri) va ProductCardDelegate (katalog kartochkasi, rasm
# bo'lmaganda to'ldiruvchi) shu bitta xaritadan foydalanadi — bitta
# manba.
_CATEGORY_ICONS = {
    "meva": "shopping-bag",
    "mevalar": "shopping-bag",
    "мева": "shopping-bag",
    "tuxum": "circle",
    "тухум": "circle",
    "shakar": "package",
    "шакар": "package",
}

DEFAULT_CATEGORY_ICON = "tag"


def icon_for_category(category):
    if not category:
        return DEFAULT_CATEGORY_ICON

    return _CATEGORY_ICONS.get(
        category.strip().lower(), DEFAULT_CATEGORY_ICON
    )
