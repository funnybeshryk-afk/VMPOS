from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.base import Base


class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id = Column(Integer, primary_key=True)

    customer_id = Column(Integer, nullable=False)
    customer_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.now)