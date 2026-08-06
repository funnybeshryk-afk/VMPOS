from app.database.database import SessionLocal
from app.models.product import Product
from app.models.stock_receipt import StockReceipt
from app.models.supplier import Supplier


class ProductService:

    @staticmethod
    def _generate_internal_barcode(session):
        barcode_number = 2000000000000

        while (
            session.query(Product.id)
            .filter(Product.barcode == str(barcode_number))
            .first()
        ):
            barcode_number += 1

        return str(barcode_number)

    @staticmethod
    def create_product(data):
        session = SessionLocal()

        try:
            barcode = data["barcode"].strip()

            if barcode:
                existing_product = (
                    session.query(Product)
                    .filter(Product.barcode == barcode)
                    .first()
                )

                if existing_product:
                    raise ValueError(
                        "Bu shtrix-kod allaqachon mavjud."
                    )
            else:
                barcode = ProductService._generate_internal_barcode(
                    session
                )

            product = Product(
                barcode=barcode,
                name=data["name"],
                category=data["category"],
                buy_price=data["buy_price"],
                sell_price=data["sell_price"],
                unit=data["unit"],
                quantity=data["quantity"],
                min_quantity=data["min_quantity"],
                description=data["description"],
            )

            session.add(product)
            session.commit()
            session.refresh(product)

            return product

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_all_products():
        session = SessionLocal()

        products = session.query(Product).all()

        session.close()

        return products

    @staticmethod
    def get_product(product_id):
        session = SessionLocal()

        product = session.get(Product, product_id)

        session.close()

        return product

    @staticmethod
    def update_product(product_id, data):
        session = SessionLocal()

        try:
            product = session.get(Product, product_id)

            if not product:
                return

            barcode = data["barcode"].strip()

            if barcode:
                existing_product = (
                    session.query(Product)
                    .filter(Product.barcode == barcode)
                    .first()
                )

                if (
                    existing_product
                    and existing_product.id != product_id
                ):
                    raise ValueError(
                        "Bu shtrix-kod allaqachon mavjud."
                    )
            else:
                barcode = (
                    product.barcode
                    or ProductService._generate_internal_barcode(session)
                )

            product.barcode = barcode
            product.name = data["name"]
            product.category = data["category"]
            product.buy_price = data["buy_price"]
            product.sell_price = data["sell_price"]
            product.unit = data["unit"]
            product.quantity = data["quantity"]
            product.min_quantity = data["min_quantity"]
            product.description = data["description"]

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def add_stock(product_id, quantity, supplier_id=None):
        if quantity <= 0:
            raise ValueError("Miqdor noldan katta bo'lishi kerak.")

        session = SessionLocal()

        try:
            product = session.get(Product, product_id)

            if product is None:
                raise ValueError("Mahsulot topilmadi.")

            supplier = None

            if supplier_id is not None:
                supplier = session.get(Supplier, supplier_id)

                if supplier is None:
                    raise ValueError(
                        "Yetkazib beruvchi topilmadi."
                    )

            product.quantity += quantity

            stock_receipt = StockReceipt(
                product_id=product.id,
                product_name=product.name,
                supplier_id=supplier.id if supplier else None,
                supplier_name=supplier.name if supplier else None,
                quantity=quantity,
            )

            session.add(stock_receipt)
            session.commit()
            session.refresh(product)

            return product

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def get_stock_receipts():
        session = SessionLocal()

        receipts = (
            session.query(StockReceipt)
            .order_by(StockReceipt.created_at.desc())
            .all()
        )

        session.close()

        return receipts

    @staticmethod
    def delete_product(product_id):
        session = SessionLocal()

        product = session.get(Product, product_id)

        if product:
            session.delete(product)
            session.commit()

        session.close()