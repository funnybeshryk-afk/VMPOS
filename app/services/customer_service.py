from app.database.database import SessionLocal
from app.models.customer import Customer
from app.models.debt_payment import DebtPayment


class CustomerService:

    @staticmethod
    def create_customer(data):
        session = SessionLocal()

        try:
            debt_amount = data["debt_amount"]
            debt_date = data["debt_date"]

            if debt_amount <= 0:
                debt_amount = 0
                debt_date = None

            customer = Customer(
                name=data["name"],
                phone=data["phone"],
                address=data["address"],
                description=data["description"],
                debt_amount=debt_amount,
                debt_date=debt_date,
            )

            session.add(customer)
            session.commit()
            session.refresh(customer)

            return customer

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_all_customers():
        session = SessionLocal()

        customers = (
            session.query(Customer)
            .order_by(Customer.name)
            .all()
        )

        session.close()

        return customers

    @staticmethod
    def get_customer(customer_id):
        session = SessionLocal()

        customer = session.get(Customer, customer_id)

        session.close()

        return customer

    @staticmethod
    def update_customer(customer_id, data):
        session = SessionLocal()

        try:
            customer = session.get(Customer, customer_id)

            if customer is None:
                return

            debt_amount = data["debt_amount"]
            debt_date = data["debt_date"]

            if debt_amount <= 0:
                debt_amount = 0
                debt_date = None

            customer.name = data["name"]
            customer.phone = data["phone"]
            customer.address = data["address"]
            customer.description = data["description"]
            customer.debt_amount = debt_amount
            customer.debt_date = debt_date

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def pay_debt(customer_id, amount):
        if amount <= 0:
            raise ValueError("To'lov summasi noldan katta bo'lishi kerak.")

        session = SessionLocal()

        try:
            customer = session.get(Customer, customer_id)

            if customer is None:
                raise ValueError("Mijoz topilmadi.")

            if customer.debt_amount <= 0:
                raise ValueError("Mijozda qarz yo'q.")

            if amount > customer.debt_amount:
                raise ValueError(
                    "To'lov summasi qarzdan katta bo'lishi mumkin emas."
                )

            customer.debt_amount -= amount

            if customer.debt_amount == 0:
                customer.debt_date = None

            payment = DebtPayment(
                customer_id=customer.id,
                customer_name=customer.name,
                amount=amount,
            )

            session.add(payment)
            session.commit()
            session.refresh(customer)

            return customer

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_debt_payments():
        session = SessionLocal()

        payments = (
            session.query(DebtPayment)
            .order_by(DebtPayment.created_at.desc())
            .all()
        )

        session.close()

        return payments

    @staticmethod
    def delete_customer(customer_id):
        session = SessionLocal()

        try:
            customer = session.get(Customer, customer_id)

            if customer:
                session.delete(customer)
                session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()