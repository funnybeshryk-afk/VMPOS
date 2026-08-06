from app.database.database import SessionLocal
from app.models.supplier import Supplier


class SupplierService:

    @staticmethod
    def create_supplier(data):
        session = SessionLocal()

        try:
            supplier = Supplier(
                name=data["name"],
                phone=data["phone"],
                address=data["address"],
                description=data["description"],
            )

            session.add(supplier)
            session.commit()
            session.refresh(supplier)

            return supplier

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_all_suppliers():
        session = SessionLocal()

        suppliers = (
            session.query(Supplier)
            .order_by(Supplier.name)
            .all()
        )

        session.close()

        return suppliers

    @staticmethod
    def get_supplier(supplier_id):
        session = SessionLocal()

        supplier = session.get(Supplier, supplier_id)

        session.close()

        return supplier

    @staticmethod
    def update_supplier(supplier_id, data):
        session = SessionLocal()

        try:
            supplier = session.get(Supplier, supplier_id)

            if supplier is None:
                return

            supplier.name = data["name"]
            supplier.phone = data["phone"]
            supplier.address = data["address"]
            supplier.description = data["description"]

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def delete_supplier(supplier_id):
        session = SessionLocal()

        try:
            supplier = session.get(Supplier, supplier_id)

            if supplier:
                session.delete(supplier)
                session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()