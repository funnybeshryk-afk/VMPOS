from sqlalchemy import Column, Integer, String, Float, Text

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