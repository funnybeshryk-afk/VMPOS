from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.base import Base


class DebtPayment(Base):
    """Mijoz qarzi bo'yicha yozuv — ikki xil turda bo'ladi.

    type="payment" — mijoz qarzni to'laydi (qarz kamayadi), eski
    yagona ma'no, CustomerService.pay_debt() orqali. type="sale" —
    Sotuv sahifasida "Nasiya" tanlanganda (qarz ortadi),
    SaleService.create_sale() orqali. Bitta jadval — chunki ikkalasi
    ham "shu mijoz bo'yicha qarz o'zgardi" degan bitta voqea, faqat
    yo'nalishi teskari; lekin "Qarz to'lovlari tarixi" oynasi faqat
    type="payment" yozuvlarini ko'rsatadi — nomi shuni va'da qiladi.

    cashier_name/cashier_user_id — Shift.cashier_name/cashier_user_id
    bilan bir xil naqsh: kassir keyin o'chirilsa/nomi o'zgarsa ham
    yozuv "surat" sifatida saqlanadi.
    """

    __tablename__ = "debt_payments"

    id = Column(Integer, primary_key=True)

    customer_id = Column(Integer, nullable=False)
    customer_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)

    type = Column(String(20), default="payment", nullable=False)
    cashier_name = Column(String(255))
    cashier_user_id = Column(Integer)
    sale_id = Column(Integer)
    shift_id = Column(Integer)

    created_at = Column(DateTime, default=datetime.now)