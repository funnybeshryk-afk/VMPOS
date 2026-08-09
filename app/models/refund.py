from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Refund(Base):
    """Bitta qaytarish operatsiyasi — bitta chekning bir yoki bir necha
    qatorini (to'liq yoki qisman) qamrab oladi.

    cashier_name/cashier_user_id — Shift.cashier_name'dagi kabi
    "surat" naqshi: kassir keyin o'chirilsa/nomi o'zgarsa ham yozuv
    o'zgarmaydi.
    """

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True)

    sale_id = Column(Integer, nullable=False)

    cashier_name = Column(String(255))
    cashier_user_id = Column(Integer)

    total_amount = Column(Float, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.now)

    items = relationship(
        "RefundItem",
        back_populates="refund",
        cascade="all, delete-orphan",
    )


class RefundItem(Base):
    __tablename__ = "refund_items"

    id = Column(Integer, primary_key=True)

    refund_id = Column(
        Integer,
        ForeignKey("refunds.id"),
        nullable=False,
    )
    sale_item_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)

    product_name = Column(String(255), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    refund = relationship("Refund", back_populates="items")
