from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database.base import Base
from app.i18n import tr

ROLE_ADMIN = "admin"
ROLE_CASHIER = "cashier"



class _RoleLabels(dict):
    """Rol nomlari: modul import paytida emas, O'QILGANDA tarjima
    qilinadi (til bazadan keyin o'rnatiladi, modellar esa undan oldin
    import qilinadi)."""

    def __getitem__(self, key):
        return tr(super().__getitem__(key))

    def get(self, key, default=None):
        if key in self:
            return self[key]

        return default


ROLE_LABELS = _RoleLabels(
    {
        ROLE_ADMIN: "Administrator",
        ROLE_CASHIER: "Kassir",
    }
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    full_name = Column(String(255), nullable=False)
    role = Column(String(20), default=ROLE_CASHIER, nullable=False)

    created_at = Column(DateTime, default=datetime.now)
