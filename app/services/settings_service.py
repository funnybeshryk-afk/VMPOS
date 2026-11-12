from app.database.database import SessionLocal
from app.models.app_setting import AppSetting
from app.utils.vat import validate_tin, validate_vat_rate


class SettingsService:

    @staticmethod
    def get_setting(key, default_value=""):
        session = SessionLocal()

        setting = (
            session.query(AppSetting)
            .filter(AppSetting.key == key)
            .first()
        )

        session.close()

        if setting is None:
            return default_value

        return setting.value or default_value

    @staticmethod
    def save_setting(key, value):
        session = SessionLocal()

        try:
            setting = (
                session.query(AppSetting)
                .filter(AppSetting.key == key)
                .first()
            )

            if setting is None:
                setting = AppSetting(
                    key=key,
                    value=value,
                )
                session.add(setting)
            else:
                setting.value = value

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_store_settings():
        return {
            "store_name": SettingsService.get_setting(
                "store_name"
            ),
            "store_phone": SettingsService.get_setting(
                "store_phone"
            ),
            "store_address": SettingsService.get_setting(
                "store_address"
            ),
        }

    @staticmethod
    def save_store_settings(data):
        SettingsService.save_setting(
            "store_name",
            data["store_name"],
        )
        SettingsService.save_setting(
            "store_phone",
            data["store_phone"],
        )
        SettingsService.save_setting(
            "store_address",
            data["store_address"],
        )

    # ---- Soliq / fiskal rekvizitlar ----------------------------------

    FISCAL_MODE_OFF = "off"

    @staticmethod
    def get_fiscal_settings():
        raw_rate = SettingsService.get_setting("default_vat_rate", "0")

        try:
            default_vat_rate = validate_vat_rate(raw_rate)
        except ValueError:
            default_vat_rate = 0.0

        return {
            "store_tin": SettingsService.get_setting("store_tin"),
            "store_legal_name": SettingsService.get_setting(
                "store_legal_name"
            ),
            # Standart QQS stavkasi (%). 0 — QQS to'lovchisi emas /
            # kiritilmagan. Mahsulotning o'z stavkasi bo'lsa, u ustun.
            "default_vat_rate": default_vat_rate or 0.0,
            # "off" — hech narsa soliq operatoriga yuborilmaydi.
            "fiscal_mode": SettingsService.get_setting(
                "fiscal_mode", SettingsService.FISCAL_MODE_OFF
            ),
        }

    @staticmethod
    def save_fiscal_settings(data):
        """Tekshiradi (ValueError) va saqlaydi. fiscal_mode bu yerda
        o'zgartirilmaydi — u provayder ulanganda alohida yoqiladi."""

        tin = validate_tin(data.get("store_tin"))
        rate = validate_vat_rate(data.get("default_vat_rate"))

        SettingsService.save_setting("store_tin", tin)
        SettingsService.save_setting(
            "store_legal_name",
            (data.get("store_legal_name") or "").strip(),
        )
        SettingsService.save_setting(
            "default_vat_rate", "0" if rate is None else f"{rate:g}"
        )
