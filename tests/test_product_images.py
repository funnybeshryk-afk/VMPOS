from app.database.migrations import prepare_database
from app.services.product_service import ProductService
from app.utils.paths import get_product_images_dir, resolve_data_path


def make_product(image_source):
    return ProductService.create_product({
        "barcode": "", "name": "Test", "category": "X", "buy_price": 1,
        "sell_price": 2, "unit": "dona", "quantity": 5, "min_quantity": 1,
        "description": "", "price_tiers": [],
        "image_source_path": str(image_source),
    })


def test_image_is_stored_with_relative_path_and_deleted_with_product(tmp_path):
    prepare_database()
    source = tmp_path / "photo.png"
    source.write_bytes(b"png")

    product = make_product(source)

    assert product.image_path.startswith("assets/products/")
    assert not product.image_path.startswith("/")
    saved = resolve_data_path(product.image_path)
    assert saved.is_file()
    assert saved.parent == get_product_images_dir()

    ProductService.delete_product(product.id)

    assert not saved.exists()
