from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database.base import Base

ROLE_ADMIN = "admin"
ROLE_CASHIER = "cashier"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrator",
    ROLE_CASHIER: "Kassir",
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    full_name = Column(String(255), nullable=False)
    role = Column(String(20), default=ROLE_CASHIER, nullable=False)

    created_at = Column(DateTime, default=datetime.now)
