from sqlalchemy import Column, Integer, String, Text

from app.database.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    address = Column(String(255))
    description = Column(Text)