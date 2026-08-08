from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    barcode = Column(String(100), unique=True)
    name = Column(String(255))
    category = Column(String(150))

    buy_price = Column(Float)
    sell_price = Column(Float)

    unit = Column(String(50))

    quantity = Column(Float)
    min_quantity = Column(Float)

    description = Column(Text)

    # assets/products/ ichidagi faylga nisbiy yo'l (masalan
    # "assets/products/<uuid>.jpg") — rasm bo'lmasa None.
    image_path = Column(String(255))

    # O'qish uchun ProductService.get_price_tiers() ishlatiladi
    # (session yopilgach lazy-load qilib bo'lmaydi) — bu relationship
    # faqat mahsulot o'chirilganda tegishli optom narxlar ham
    # avtomatik o'chishi uchun kerak (cascade).
    price_tiers = relationship(
        "PriceTier",
        back_populates="product",
        cascade="all, delete-orphan",
    )