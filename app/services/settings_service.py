from app.database.database import SessionLocal
from app.models.app_setting import AppSetting


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