"""Dastur versiyasi va baza sxemasi versiyasi — yagona manba.

APP_VERSION — foydalanuvchi ko'radigan versiya (oyna sarlavhasi,
kelajakda avtomatik yangilash tekshiruvi).

SCHEMA_VERSION — ma'lumotlar bazasi tuzilmasi versiyasi. U SQLite'ning
`PRAGMA user_version` maydonida saqlanadi. Bazaga yangi ustun/jadval
qo'shadigan har bir o'zgarishda uni 1 ga OSHIRING va
app/database/migrations.py'ga mos migratsiyani qo'shing. Shu tufayli:
  * eski dastur yangi bazani ochmaydi (jimgina noto'g'ri ishlamaydi);
  * migratsiyadan oldin baza avtomatik zaxiralanadi.
"""

APP_VERSION = "1.2.2"

SCHEMA_VERSION = 1
