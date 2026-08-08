from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.base import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)

    opened_at = Column(DateTime, default=datetime.now, nullable=False)
    closed_at = Column(DateTime)

    # StockReceipt.supplier_id/supplier_name'dagi kabi — cashier_name
    # tarixiy "surat" sifatida saqlanadi (Foydalanuvchi keyin
    # o'chirilsa/nomi o'zgarsa ham smena yozuvi buzilmaydi),
    # cashier_user_id esa joriy Foydalanuvchiga ixtiyoriy bog'lanish.
    cashier_name = Column(String(255), nullable=False)
    cashier_user_id = Column(Integer)

    opening_cash_amount = Column(Float, default=0, nullable=False)
    closing_cash_amount = Column(Float)
    expected_cash_amount = Column(Float)
    cash_difference = Column(Float)

    # Smena yopilganda hisoblab, shu yerga "suratga olingan" holda
    # yoziladi — keyinchalik Sale yozuvlari o'zgarsa ham (masalan,
    # qaytarilsa), Z-hisobot o'sha paytdagi holatini saqlab qoladi.
    sales_count = Column(Integer, default=0, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)
    cash_total = Column(Float, default=0, nullable=False)
    card_total = Column(Float, default=0, nullable=False)

    status = Column(String(20), default="open", nullable=False)
