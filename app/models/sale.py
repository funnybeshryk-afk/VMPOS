from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    total_amount = Column(Float, default=0)

    payment_method = Column(String(20), default="cash", nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)
    change_amount = Column(Float, default=0, nullable=False)

    status = Column(
        String(20),
        default="completed",
        nullable=False,
    )

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True)

    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        nullable=False,
    )
    product_id = Column(Integer, nullable=False)

    product_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")