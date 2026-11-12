"""Animatsiyalar: umumiy yoqish/o'chirish va davomiyliklar.

Qoidalar:
  * animatsiyalar QISQA (<= ~260 ms) va hech qachon kiritishni bloklamaydi
    (hammasi QVariantAnimation/QPropertyAnimation — voqealar sikli
    ishlayveradi, tugma bosilsa darhol qayta ishlanadi);
  * "Sozlamalar"da o'chirish mumkin (sekin kompyuterlar uchun); o'chiq
    bo'lsa hamma narsa darhol, animatsiyasiz o'zgaradi;
  * natija animatsiyasiz bilan bir xil bo'lishi shart (oxirgi kadr —
    aniq yakuniy qiymat), shuning uchun mantiq animatsiyaga bog'liq emas.
"""

import os

SETTING_KEY = "animations_enabled"

DURATION_TOTAL_MS = 220    # jami summa "docrutka"
DURATION_ROW_MS = 200      # korzinaga yangi qator chiqishi
DURATION_FLASH_MS = 260    # katalogda kartochka "vspishka"

_enabled = True


def is_enabled():
    return _enabled


def set_enabled(value):
    global _enabled

    _enabled = bool(value)


def load_from_settings():
    """Dastur ochilganda: saqlangan sozlama (standart — yoqilgan).
    VMPOS_NO_ANIM=1 muhit o'zgaruvchisi hamma narsani majburan o'chiradi
    (sekin/uzoqdan ishlatiladigan kompyuterlar, diagnostika)."""

    if os.environ.get("VMPOS_NO_ANIM") == "1":
        set_enabled(False)
        return

    # Kechiktirilgan import — bu modul bazasiz ham import qilinadi.
    from app.services.settings_service import SettingsService

    value = SettingsService.get_setting(SETTING_KEY, "1")
    set_enabled(value != "0")


def save_enabled(value):
    from app.services.settings_service import SettingsService

    set_enabled(value)
    SettingsService.save_setting(SETTING_KEY, "1" if value else "0")
