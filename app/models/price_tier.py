from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.base import Base


class PriceTier(Base):
    __tablename__ = "price_tiers"

    id = Column(Integer, primary_key=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    # Og'irlik bo'yicha sotiladigan tovarlarda (kg) miqdor kasr
    # bo'lishi mumkin, shuning uchun Integer emas — Product.quantity
    # bilan bir xil turdagi Float.
    min_quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="price_tiers")
