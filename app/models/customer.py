from sqlalchemy import Column, Date, Float, Integer, String, Text

from app.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    address = Column(String(255))
    description = Column(Text)

    debt_amount = Column(Float, default=0, nullable=False)
    debt_date = Column(Date)