from datetime import datetime, timedelta

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.services.product_service import ProductService


class SaleService:

    @staticmethod
    def create_sale(
        cart,
        payment_method,
        paid_amount,
        cash_amount=None,
        card_amount=None,
    ):
        session = SessionLocal()

        try:
            total_amount = 0
            products = {}
            unit_prices = {}

            for item in cart.values():
                cart_product = item["product"]
                quantity = item["quantity"]

                product = session.get(Product, cart_product.id)

                if product is None:
                    raise ValueError(
                        f"Mahsulot topilmadi: {cart_product.name}"
                    )

                if product.quantity < quantity:
                    raise ValueError(
                        f"Qoldiq yetarli emas: {product.name}"
                    )

                # Narx bu yerda, checkout paytida, serverda qayta
                # hisoblanadi — optom narx daraja jadvali savat
                # yig'ilayotgan paytdan keyin o'zgargan bo'lishi
                # mumkin, shuning uchun UI ko'rsatgan narxga
                # ishonilmaydi.
                unit_price = ProductService.resolve_price(
                    product, quantity
                )

                products[product.id] = product
                unit_prices[product.id] = unit_price
                total_amount += unit_price * quantity

            if payment_method == "cash" and paid_amount < total_amount:
                raise ValueError("Berilgan summa yetarli emas.")

            if payment_method == "card":
                paid_amount = total_amount

            if payment_method == "mixed":
                if cash_amount is None or card_amount is None:
                    raise ValueError(
                        "Aralash to'lov summalari ko'rsatilmagan."
                    )

                if cash_amount < 0 or card_amount < 0:
                    raise ValueError(
                        "Summalar manfiy bo'lishi mumkin emas."
                    )

                if (
                    abs((cash_amount + card_amount) - total_amount)
                    > 0.01
                ):
                    raise ValueError(
                        "Naqd va karta summalari jami chek "
                        "summasiga teng emas."
                    )

                paid_amount = cash_amount + card_amount

            elif payment_method == "card":
                cash_amount = 0
                card_amount = total_amount

            else:
                cash_amount = total_amount
                card_amount = 0

            change_amount = paid_amount - total_amount

            sale = Sale(
                total_amount=total_amount,
                payment_method=payment_method,
                paid_amount=paid_amount,
                change_amount=change_amount,
                cash_amount=cash_amount,
                card_amount=card_amount,
                status="completed",
            )
            session.add(sale)
            session.flush()

            for product_id, item in cart.items():
                product = products[product_id]
                quantity = item["quantity"]
                unit_price = unit_prices[product_id]
                line_total = unit_price * quantity

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    product_name=product.name,
                    price=unit_price,
                    quantity=quantity,
                    line_total=line_total,
                )

                product.quantity -= quantity
                session.add(sale_item)

            session.commit()
            session.refresh(sale)

            return sale

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def refund_sale(sale_id):
        session = SessionLocal()

        try:
            sale = session.get(Sale, sale_id)

            if sale is None:
                raise ValueError("Chek topilmadi.")

            if sale.status == "refunded":
                raise ValueError("Bu chek allaqachon qaytarilgan.")

            sale_items = (
                session.query(SaleItem)
                .filter(SaleItem.sale_id == sale_id)
                .all()
            )

            for sale_item in sale_items:
                product = session.get(Product, sale_item.product_id)

                if product is not None:
                    product.quantity += sale_item.quantity

            sale.status = "refunded"

            session.commit()
            session.refresh(sale)

            return sale

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_all_sales():
        session = SessionLocal()

        sales = (
            session.query(Sale)
            .order_by(Sale.created_at.desc())
            .all()
        )

        session.close()

        return sales

    @staticmethod
    def get_sales_by_date(selected_date):
        session = SessionLocal()

        day_start = datetime.combine(
            selected_date,
            datetime.min.time(),
        )
        next_day_start = day_start + timedelta(days=1)

        sales = (
            session.query(Sale)
            .filter(Sale.created_at >= day_start)
            .filter(Sale.created_at < next_day_start)
            .order_by(Sale.created_at.desc())
            .all()
        )

        session.close()

        return sales

    @staticmethod
    def get_sale_items(sale_id):
        session = SessionLocal()

        sale_items = (
            session.query(SaleItem)
            .filter(SaleItem.sale_id == sale_id)
            .order_by(SaleItem.id)
            .all()
        )

        session.close()

        return sale_items

    @staticmethod
    def get_summary_by_date(selected_date):
        sales = SaleService.get_sales_by_date(selected_date)

        total_amount = 0
        cash_total = 0
        card_total = 0
        sales_count = 0

        for sale in sales:
            if sale.status != "completed":
                continue

            sales_count += 1
            total_amount += sale.total_amount
            # cash_amount/card_amount orqali hisoblanadi, payment_method
            # orqali emas — "mixed" savdoda ikkalasi ham > 0 bo'ladi,
            # va u avval to'liq "naqd"ga tushib qolardi.
            cash_total += sale.cash_amount
            card_total += sale.card_amount

        return {
            "sales_count": sales_count,
            "total_amount": total_amount,
            "cash_total": cash_total,
            "card_total": card_total,
        }

    @staticmethod
    def get_today_summary():
        return SaleService.get_summary_by_date(
            datetime.now().date()
        )