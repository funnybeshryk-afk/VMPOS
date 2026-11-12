"""Fiskalizatsiya holati (hozircha faqat tayyorlov — hech narsa yuborilmaydi).

Provayder (virtual kassa / fiskal modul / integrator) tanlanganda shu
yerga yuborish navbati va qayta urinishlar qo'shiladi. Hozir esa bitta
savol: yangi chek/qaytarish uchun boshlang'ich fiskal holat qanday.
"""

from app.models.fiscal import FISCAL_NONE, FISCAL_PENDING, FISCAL_SENT
from app.services.settings_service import SettingsService


class FiscalService:

    @staticmethod
    def is_enabled():
        mode = SettingsService.get_fiscal_settings()["fiscal_mode"]

        return mode != SettingsService.FISCAL_MODE_OFF

    @staticmethod
    def initial_sale_status():
        """Yangi chek: fiskalizatsiya yoqilgan bo'lsa — navbatga
        ("pending"), aks holda hech narsa ("none")."""

        return FISCAL_PENDING if FiscalService.is_enabled() else FISCAL_NONE

    @staticmethod
    def initial_refund_status(sale):
        """Qaytarish faqat ASL chek fiskallashtirilgan bo'lsa fiskal
        qaytarish chekini talab qiladi."""

        if FiscalService.is_enabled() and sale.fiscal_status in (
            FISCAL_SENT,
            FISCAL_PENDING,
        ):
            return FISCAL_PENDING

        return FISCAL_NONE
