from app.database.database import SessionLocal
from app.models.shift import Shift
from app.models.user import ROLE_ADMIN, ROLE_CASHIER, User

_VALID_ROLES = {ROLE_ADMIN, ROLE_CASHIER}


class UserService:

    @staticmethod
    def get_all_users():
        session = SessionLocal()

        users = (
            session.query(User)
            .order_by(User.full_name)
            .all()
        )

        session.close()

        return users

    @staticmethod
    def get_user(user_id):
        session = SessionLocal()

        user = session.get(User, user_id)

        session.close()

        return user

    @staticmethod
    def create_user(data):
        full_name = (data.get("full_name") or "").strip()
        role = data.get("role")

        if not full_name:
            raise ValueError("Foydalanuvchi ismini kiriting.")

        if role not in _VALID_ROLES:
            raise ValueError("Rol noto'g'ri tanlandi.")

        session = SessionLocal()

        try:
            user = User(full_name=full_name, role=role)

            session.add(user)
            session.commit()
            session.refresh(user)

            return user

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def update_user(user_id, data):
        full_name = (data.get("full_name") or "").strip()
        role = data.get("role")

        if not full_name:
            raise ValueError("Foydalanuvchi ismini kiriting.")

        if role not in _VALID_ROLES:
            raise ValueError("Rol noto'g'ri tanlandi.")

        session = SessionLocal()

        try:
            user = session.get(User, user_id)

            if user is None:
                return None

            if user.role == ROLE_ADMIN and role != ROLE_ADMIN:
                UserService._ensure_not_last_admin(session, user_id)

            user.full_name = full_name
            user.role = role

            session.commit()
            session.refresh(user)

            return user

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def delete_user(user_id):
        session = SessionLocal()

        try:
            user = session.get(User, user_id)

            if user is None:
                return

            if user.role == ROLE_ADMIN:
                UserService._ensure_not_last_admin(session, user_id)

            open_shift = (
                session.query(Shift)
                .filter(Shift.status == "open")
                .filter(Shift.cashier_user_id == user_id)
                .first()
            )

            if open_shift is not None:
                raise ValueError(
                    "Bu foydalanuvchi hozir ochiq smenaga "
                    "biriktirilgan."
                )

            session.delete(user)
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def _ensure_not_last_admin(session, user_id):
        other_admins = (
            session.query(User)
            .filter(User.role == ROLE_ADMIN)
            .filter(User.id != user_id)
            .count()
        )

        if other_admins == 0:
            raise ValueError(
                "Kamida bitta Administrator qolishi kerak."
            )
