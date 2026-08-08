import shutil
import uuid
from pathlib import Path

from app.database.database import SessionLocal
from app.models.price_tier import PriceTier
from app.models.product import Product
from app.models.stock_receipt import StockReceipt
from app.models.supplier import Supplier

_PRODUCT_IMAGES_DIR = Path("assets/products")


class ProductService:

    @staticmethod
    def _save_product_image(source_path):
        """Tanlangan rasmni assets/products/ ichiga nusxalaydi.

        Fayl nomi UUID bilan berilgan — asl fayl nomidagi ziddiyat
        yoki maxsus belgilar (masalan bo'sh joy) haqida qayg'urishga
        hojat qolmaydi, bitta mahsulotga bitta noyob fayl.
        """

        _PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        extension = Path(source_path).suffix.lower()
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = _PRODUCT_IMAGES_DIR / filename

        shutil.copyfile(source_path, destination)

        return destination.as_posix()

    @staticmethod
    def _delete_product_image(image_path):
        if not image_path:
            return

        try:
            Path(image_path).unlink(missing_ok=True)
        except OSError:
            pass

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
    def _validate_price_tiers(price_tiers):
        seen_min_quantities = set()
        validated = []

        for tier in price_tiers:
            min_quantity = tier["min_quantity"]
            price = tier["price"]

            if min_quantity <= 0:
                raise ValueError(
                    "Optom narx miqdori noldan katta bo'lishi "
                    "kerak."
                )

            if price <= 0:
                raise ValueError(
                    "Optom narx noldan katta bo'lishi kerak."
                )

            if min_quantity in seen_min_quantities:
                raise ValueError(
                    "Optom narxlar orasida miqdor takrorlanmasligi "
                    "kerak."
                )

            seen_min_quantities.add(min_quantity)
            validated.append({
                "min_quantity": min_quantity,
                "price": price,
            })

        validated.sort(key=lambda tier: tier["min_quantity"])

        return validated

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

            price_tiers = ProductService._validate_price_tiers(
                data.get("price_tiers") or []
            )

            image_path = None

            if data.get("image_source_path"):
                image_path = ProductService._save_product_image(
                    data["image_source_path"]
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
                image_path=image_path,
            )

            session.add(product)
            session.flush()

            for tier in price_tiers:
                session.add(
                    PriceTier(
                        product_id=product.id,
                        min_quantity=tier["min_quantity"],
                        price=tier["price"],
                    )
                )

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

            price_tiers = ProductService._validate_price_tiers(
                data.get("price_tiers") or []
            )

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

            # Rasm ustuni faqat foydalanuvchi uni bevosita o'zgartirsa
            # tegiladi — aks holda (na "olib tashlash" bosilgan, na
            # yangi fayl tanlangan) eski image_path saqlanib qoladi.
            if data.get("remove_image"):
                ProductService._delete_product_image(
                    product.image_path
                )
                product.image_path = None
            elif data.get("image_source_path"):
                ProductService._delete_product_image(
                    product.image_path
                )
                product.image_path = (
                    ProductService._save_product_image(
                        data["image_source_path"]
                    )
                )

            # Dialog har doim to'liq ro'yxatni yuboradi (qo'shilgan/
            # o'chirilgan qatorlar allaqachon hisobga olingan) —
            # shuning uchun eskilarini o'chirib, yangilarini qayta
            # yozish diff qilishdan soddaroq va xatoga kamroq beriladi.
            session.query(PriceTier).filter(
                PriceTier.product_id == product_id
            ).delete()

            for tier in price_tiers:
                session.add(
                    PriceTier(
                        product_id=product_id,
                        min_quantity=tier["min_quantity"],
                        price=tier["price"],
                    )
                )

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
            ProductService._delete_product_image(product.image_path)
            session.delete(product)
            session.commit()

        session.close()

    @staticmethod
    def get_price_tiers(product_id):
        session = SessionLocal()

        price_tiers = (
            session.query(PriceTier)
            .filter(PriceTier.product_id == product_id)
            .order_by(PriceTier.min_quantity)
            .all()
        )

        session.close()

        return price_tiers

    @staticmethod
    def resolve_price(product, quantity):
        """Berilgan miqdorga mos narxni tanlaydi.

        Optom narxlar bo'yicha kamayib bo'lmaydigan tartibda —
        quantity'dan oshmagan eng katta min_quantity'ning narxi
        qo'llanadi. Hech qanday daraja mos kelmasa (yoki umuman
        belgilanmagan bo'lsa) — mahsulotning oddiy sotish narxi.
        """

        applicable_price = product.sell_price

        for tier in ProductService.get_price_tiers(product.id):
            if quantity >= tier.min_quantity:
                applicable_price = tier.price

        return applicable_price