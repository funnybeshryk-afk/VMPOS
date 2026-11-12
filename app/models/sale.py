from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.fiscal import FiscalFieldsMixin


class Sale(FiscalFieldsMixin, Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    total_amount = Column(Float, default=0)

    payment_method = Column(String(20), default="cash", nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)
    change_amount = Column(Float, default=0, nullable=False)

    # "cash"/"card" savdolarda bittasi total_amount'ga teng, ikkinchisi 0.
    # "mixed"da ikkalasi ham > 0 va yig'indisi total_amount'ga teng bo'ladi.
    # Hisobotlarda naqd/karta bo'yicha to'g'ri taqsimlash shu ikki ustunga
    # tayanadi — payment_method bo'yicha emas (mixed'ni ham ajratish uchun).
    cash_amount = Column(Float, default=0, nullable=False)
    card_amount = Column(Float, default=0, nullable=False)

    # "completed" -> "partially_refunded" (ba'zi qatorlar qisman
    # qaytarilgan) -> "refunded" (barcha qatorlar to'liq qaytarilgan).
    # SaleItem.returned_quantity asosida RefundService hisoblaydi.
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

    # Shu qatordan qancha miqdor qaytarilgani — bir nechta qisman
    # qaytarish operatsiyasida ustma-ust to'planadi. Qoldiq (yana
    # qancha qaytarish mumkin) = quantity - returned_quantity.
    returned_quantity = Column(Float, default=0, nullable=False)

    # Sotuv paytidagi "surat" (mahsulot keyin o'zgarsa ham chek
    # o'zgarmaydi): IKPU, qadoq kodi, QQS stavkasi va summasi.
    ikpu_code = Column(String(20))
    package_code = Column(String(20))
    vat_rate = Column(Float, default=0, nullable=False)
    vat_amount = Column(Float, default=0, nullable=False)

    sale = relationship("Sale", back_populates="items")