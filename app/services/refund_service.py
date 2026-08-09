from app.database.database import SessionLocal
from app.models.customer import Customer
from app.models.debt_payment import DebtPayment
from app.models.product import Product
from app.models.refund import Refund, RefundItem
from app.models.sale import Sale, SaleItem

_TOLERANCE = 0.001


class RefundService:

    @staticmethod
    def create_refund(
        sale_id,
        items,
        cashier_name=None,
        cashier_user_id=None,
    ):
        """Chekning bir yoki bir nechta qatorini (to'liq/qisman) qaytarish.

        items: [{"sale_item_id": int, "quantity": float}, ...]

        Qaytarilgan miqdor SaleItem.returned_quantity'ga qo'shiladi
        (bir nechta qisman qaytarish ustma-ust to'planadi — shuning
        uchun bir qatorni ikki marta qisman qaytarish mumkin, lekin
        jami qoldiqdan oshib ketmaydi), mahsulot ombor qoldig'iga
        qaytadi, chekning moliyaviy maydonlari (total/cash/card/paid)
        qaytarilgan summaga mos kamayadi.

        Naqd/karta ulushi orqali kamaytiriladi — Nasiya chekda
        cash_amount+card_amount total_amount'dan kichik bo'ladi
        (qolgan farq — mijoz qarziga yozilgan qism), shuning uchun
        shu farq nisbatan "qarz ulushi" sifatida hisoblanadi va
        tegishli mijozning qarzidan ham ayiriladi.
        """

        session = SessionLocal()

        try:
            sale = session.get(Sale, sale_id)

            if sale is None:
                raise ValueError("Chek topilmadi.")

            if sale.status == "refunded":
                raise ValueError(
                    "Bu chek allaqachon to'liq qaytarilgan."
                )

            if not items:
                raise ValueError(
                    "Qaytariladigan mahsulot tanlanmagan."
                )

            original_total = sale.total_amount

            refund = Refund(
                sale_id=sale.id,
                cashier_name=cashier_name,
                cashier_user_id=cashier_user_id,
                total_amount=0,
            )
            session.add(refund)
            session.flush()

            total_refund = 0

            for entry in items:
                quantity = entry["quantity"]

                if quantity <= 0:
                    continue

                sale_item = session.get(
                    SaleItem, entry["sale_item_id"]
                )

                if sale_item is None or sale_item.sale_id != sale.id:
                    raise ValueError("Chek qatori topilmadi.")

                remaining = (
                    sale_item.quantity - sale_item.returned_quantity
                )

                if quantity > remaining + _TOLERANCE:
                    raise ValueError(
                        f"{sale_item.product_name}: qaytarish "
                        "miqdori qoldiqdan katta bo'lishi mumkin "
                        "emas."
                    )

                line_total = sale_item.price * quantity
                total_refund += line_total

                sale_item.returned_quantity += quantity

                product = session.get(Product, sale_item.product_id)

                if product is not None:
                    product.quantity += quantity

                session.add(
                    RefundItem(
                        refund_id=refund.id,
                        sale_item_id=sale_item.id,
                        product_id=sale_item.product_id,
                        product_name=sale_item.product_name,
                        unit_price=sale_item.price,
                        quantity=quantity,
                        line_total=line_total,
                    )
                )

            if total_refund <= 0:
                raise ValueError(
                    "Qaytariladigan mahsulot tanlanmagan."
                )

            if original_total > _TOLERANCE:
                cash_ratio = sale.cash_amount / original_total
                card_ratio = sale.card_amount / original_total
            else:
                cash_ratio = 0
                card_ratio = 0

            refunded_cash = total_refund * cash_ratio
            refunded_card = total_refund * card_ratio
            refunded_debt = (
                total_refund - refunded_cash - refunded_card
            )

            sale.cash_amount = max(
                0, sale.cash_amount - refunded_cash
            )
            sale.card_amount = max(
                0, sale.card_amount - refunded_card
            )
            sale.paid_amount = max(
                0,
                sale.paid_amount - (refunded_cash + refunded_card),
            )
            sale.total_amount = max(
                0, sale.total_amount - total_refund
            )

            if (
                refunded_debt > _TOLERANCE
                and sale.payment_method == "debt"
            ):
                debt_link = (
                    session.query(DebtPayment)
                    .filter(DebtPayment.sale_id == sale.id)
                    .filter(DebtPayment.type == "sale")
                    .first()
                )

                if debt_link is not None:
                    customer = session.get(
                        Customer, debt_link.customer_id
                    )

                    if customer is not None:
                        customer.debt_amount = max(
                            0,
                            customer.debt_amount - refunded_debt,
                        )

                        if customer.debt_amount <= 0:
                            customer.debt_date = None

            all_sale_items = (
                session.query(SaleItem)
                .filter(SaleItem.sale_id == sale.id)
                .all()
            )

            fully_returned = all(
                item.returned_quantity
                >= item.quantity - _TOLERANCE
                for item in all_sale_items
            )

            sale.status = (
                "refunded" if fully_returned else "partially_refunded"
            )

            refund.total_amount = total_refund

            session.commit()
            session.refresh(refund)

            return refund

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_refund_history():
        session = SessionLocal()

        refunds = (
            session.query(Refund)
            .order_by(Refund.created_at.desc())
            .all()
        )

        session.close()

        return refunds
