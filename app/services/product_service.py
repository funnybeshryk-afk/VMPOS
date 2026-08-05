from app.database.database import SessionLocal
from app.models.product import Product


class ProductService:

    @staticmethod
    def create_product(data):
        session = SessionLocal()

        product = Product(
            barcode=data["barcode"],
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
        session.close()

        return product

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

        product = session.get(Product, product_id)

        if product:
            product.barcode = data["barcode"]
            product.name = data["name"]
            product.category = data["category"]
            product.buy_price = data["buy_price"]
            product.sell_price = data["sell_price"]
            product.unit = data["unit"]
            product.quantity = data["quantity"]
            product.min_quantity = data["min_quantity"]
            product.description = data["description"]

            session.commit()

        session.close()

    @staticmethod
    def delete_product(product_id):
        session = SessionLocal()

        product = session.get(Product, product_id)

        if product:
            session.delete(product)
            session.commit()

        session.close()