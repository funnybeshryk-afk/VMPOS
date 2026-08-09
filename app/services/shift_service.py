from datetime import datetime

from app.database.database import SessionLocal
from app.models.sale import Sale
from app.models.shift import Shift


class ShiftService:

    @staticmethod
    def _summarize_sales_between(start, end):
        session = SessionLocal()

        sales = (
            session.query(Sale)
            .filter(Sale.created_at >= start)
            .filter(Sale.created_at <= end)
            .all()
        )

        session.close()

        sales_count = 0
        total_amount = 0
        cash_total = 0
        card_total = 0

        for sale in sales:
            # SaleService.get_summary_by_date'dagi kabi — to'liq
            # qaytarilgan chek chiqarib tashlanadi, qisman qaytarilgan
            # esa (RefundService tomonidan allaqachon kamaytirilgan
            # summalari bilan) hisobga kiradi.
            if sale.status == "refunded":
                continue

            sales_count += 1
            total_amount += sale.total_amount
            # SaleService.get_summary_by_date'dagi kabi —
            # cash_amount/card_amount orqali, payment_method orqali emas,
            # aks holda "mixed" savdo to'liq naqdga tushib qolardi.
            cash_total += sale.cash_amount
            card_total += sale.card_amount

        return {
            "sales_count": sales_count,
            "total_amount": total_amount,
            "cash_total": cash_total,
            "card_total": card_total,
        }

    @staticmethod
    def get_open_shift():
        session = SessionLocal()

        shift = (
            session.query(Shift)
            .filter(Shift.status == "open")
            .first()
        )

        session.close()

        return shift

    @staticmethod
    def get_all_shifts():
        session = SessionLocal()

        shifts = (
            session.query(Shift)
            .order_by(Shift.opened_at.desc())
            .all()
        )

        session.close()

        return shifts

    @staticmethod
    def get_shift_preview(shift):
        """Ochiq smenaning joriy (hali yakunlanmagan) hisobi."""
        return ShiftService._summarize_sales_between(
            shift.opened_at, datetime.now()
        )

    @staticmethod
    def open_shift(
        cashier_name, opening_cash_amount, cashier_user_id=None
    ):
        cashier_name = (cashier_name or "").strip()

        if not cashier_name:
            raise ValueError("Kassir ismini kiriting.")

        if opening_cash_amount < 0:
            raise ValueError(
                "Boshlang'ich summa manfiy bo'lishi mumkin emas."
            )

        session = SessionLocal()

        try:
            existing_open_shift = (
                session.query(Shift)
                .filter(Shift.status == "open")
                .first()
            )

            if existing_open_shift is not None:
                raise ValueError("Allaqachon ochiq smena mavjud.")

            shift = Shift(
                cashier_name=cashier_name,
                cashier_user_id=cashier_user_id,
                opening_cash_amount=opening_cash_amount,
                status="open",
            )
            session.add(shift)
            session.commit()
            session.refresh(shift)

            return shift

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def close_shift(shift_id, closing_cash_amount):
        if closing_cash_amount < 0:
            raise ValueError(
                "Kassadagi summa manfiy bo'lishi mumkin emas."
            )

        session = SessionLocal()

        try:
            shift = session.get(Shift, shift_id)

            if shift is None:
                raise ValueError("Smena topilmadi.")

            if shift.status != "open":
                raise ValueError("Bu smena allaqachon yopilgan.")

            summary = ShiftService._summarize_sales_between(
                shift.opened_at, datetime.now()
            )

            expected_cash_amount = (
                shift.opening_cash_amount + summary["cash_total"]
            )

            shift.closed_at = datetime.now()
            shift.sales_count = summary["sales_count"]
            shift.total_amount = summary["total_amount"]
            shift.cash_total = summary["cash_total"]
            shift.card_total = summary["card_total"]
            shift.closing_cash_amount = closing_cash_amount
            shift.expected_cash_amount = expected_cash_amount
            shift.cash_difference = (
                closing_cash_amount - expected_cash_amount
            )
            shift.status = "closed"

            session.commit()
            session.refresh(shift)

            return shift

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
