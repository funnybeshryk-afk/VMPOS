from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.base import Base


class StockReceipt(Base):
    __tablename__ = "stock_receipts"

    id = Column(Integer, primary_key=True)

    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)

    supplier_id = Column(Integer)
    supplier_name = Column(String(255))

    quantity = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.now)