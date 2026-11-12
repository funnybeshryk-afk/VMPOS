from datetime import datetime
from types import SimpleNamespace

from app.services.sale_service import SaleService
from app.services.settings_service import SettingsService
from app.utils import receipt_render
from app.utils.receipt import DEFAULT_FOOTER, build_receipt
from app.utils.receipt_render import ReceiptPrintError, render_receipt

__all__ = ["ReceiptService", "ReceiptPrintError"]

_VALID_PAPERS = ("58", "80")
_FOOTER_MAX = 200


class ReceiptService:
    """Chek sozlamalari, tuzish va chop etish. FISKAL emas."""

    # ---- sozlamalar ----------------------------------------------

    @staticmethod
    def get_settings():
        paper = SettingsService.get_setting("receipt_paper_mm", "80")

        # Pastki yozuv: foydalanuvchi saqlagan bo'lsa (bo'sh bo'lsa ham —
        # "yozuvsiz"), aks holda standart matn.
        if SettingsService.get_setting("receipt_footer_set", "0") == "1":
            footer = SettingsService.get_setting("receipt_footer", "")
        else:
            footer = DEFAULT_FOOTER

        return {
            # "" — tizimdagi standart printer.
            "printer": SettingsService.get_setting("receipt_printer", ""),
            "paper_mm": paper if paper in _VALID_PAPERS else "80",
            "auto_print": SettingsService.get_setting("receipt_auto_print", "0") == "1",
            "footer": footer,
            "show_barcode": SettingsService.get_setting("receipt_barcode", "1") == "1",
        }

    @staticmethod
    def save_settings(data):
        paper = str(data.get("paper_mm", "80"))

        if paper not in _VALID_PAPERS:
            raise ValueError("Qog'oz kengligi 58 yoki 80 mm bo'lishi kerak.")

        footer = (data.get("footer") or "").strip()

        if len(footer) > _FOOTER_MAX:
            raise ValueError(f"Pastki yozuv {_FOOTER_MAX} belgidan oshmasligi kerak.")

        SettingsService.save_setting("receipt_printer", data.get("printer") or "")
        SettingsService.save_setting("receipt_paper_mm", paper)
        SettingsService.save_setting("receipt_auto_print", "1" if data.get("auto_print") else "0")
        # Bo'sh pastki yozuv — ataylab "yozuvsiz" (standart emas), shuning
        # uchun "o'rnatilgan" belgisi alohida saqlanadi.
        SettingsService.save_setting("receipt_footer", footer)
        SettingsService.save_setting("receipt_footer_set", "1")
        SettingsService.save_setting("receipt_barcode", "1" if data.get("show_barcode", True) else "0")

    @staticmethod
    def list_printers():
        return receipt_render.available_printers()

    # ---- tuzish ----------------------------------------------------

    @staticmethod
    def _store_info():
        info = dict(SettingsService.get_store_settings())
        fiscal = SettingsService.get_fiscal_settings()
        info["store_tin"] = fiscal["store_tin"]
        info["store_legal_name"] = fiscal["store_legal_name"]

        return info

    @staticmethod
    def _options(settings):
        return {
            "footer": settings["footer"],
            "show_barcode": settings["show_barcode"],
            "non_fiscal_note": True,
        }

    @staticmethod
    def build_for_sale(sale_id):
        sale = SaleService.get_sale(sale_id)

        if sale is None:
            raise ValueError("Chek topilmadi.")

        items = SaleService.get_sale_items(sale_id)
        settings = ReceiptService.get_settings()

        return build_receipt(
            sale, items, ReceiptService._store_info(), ReceiptService._options(settings)
        )

    @staticmethod
    def build_sample():
        """Sinov cheki: haqiqiy savdosiz, namunaviy ma'lumot bilan."""

        sale = SimpleNamespace(
            id=1, created_at=datetime.now(), status="completed",
            total_amount=48500.0, paid_amount=50000.0, change_amount=1500.0,
            cash_amount=48500.0, card_amount=0.0, payment_method="cash",
            vat_total=0.0, fiscal_status="none",
        )
        items = [
            SimpleNamespace(product_name="Sinov mahsuloti 1", quantity=2, price=12000.0,
                            line_total=24000.0, vat_rate=0.0, vat_amount=0.0),
            SimpleNamespace(product_name="Sinov mahsuloti uzun nomi bilan, qatorga sig'masa o'raladi",
                            quantity=1, price=24500.0, line_total=24500.0,
                            vat_rate=0.0, vat_amount=0.0),
        ]
        settings = ReceiptService.get_settings()

        return build_receipt(
            sale, items, ReceiptService._store_info(), ReceiptService._options(settings)
        )

    # ---- chizish / chop etish -------------------------------------

    @staticmethod
    def render(receipt, antialias=True):
        return render_receipt(receipt, ReceiptService.get_settings()["paper_mm"], antialias)

    @staticmethod
    def print_receipt(receipt, pdf_path=None):
        settings = ReceiptService.get_settings()
        image = render_receipt(receipt, settings["paper_mm"], antialias=False)

        receipt_render.print_image(
            image, settings["paper_mm"], settings["printer"], pdf_path
        )

    @staticmethod
    def print_sale(sale_id, pdf_path=None):
        """Chekni chop etadi (yoki pdf_path'ga saqlaydi).
        ReceiptPrintError ko'tarishi mumkin."""

        ReceiptService.print_receipt(ReceiptService.build_for_sale(sale_id), pdf_path)

    @staticmethod
    def print_test(pdf_path=None):
        ReceiptService.print_receipt(ReceiptService.build_sample(), pdf_path)
