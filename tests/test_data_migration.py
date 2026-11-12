import sqlite3

from app.utils.data_migration import migrate_legacy_data
from app.utils.paths import (
    get_data_dir,
    resolve_data_path,
    to_data_relative,
)


def make_legacy(legacy, image_name="a1.png", abs_path=True):
    legacy.mkdir()
    (legacy / "assets" / "products").mkdir(parents=True)
    (legacy / "assets" / "products" / image_name).write_bytes(b"png")
    (legacy / "backups").mkdir()
    (legacy / "backups" / "vmpos_old.db").write_bytes(b"old")

    image_path = (
        (legacy / "assets" / "products" / image_name).as_posix()
        if abs_path
        else f"assets/products/{image_name}"
    )
    connection = sqlite3.connect(str(legacy / "vmpos.db"))
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, image_path TEXT)"
    )
    connection.execute(
        "INSERT INTO products (name, image_path) VALUES ('Non', ?), ('Suv', NULL)",
        (image_path,),
    )
    connection.commit()
    connection.close()


def test_legacy_data_is_copied_and_image_paths_become_relative(tmp_path):
    legacy, new = tmp_path / "exe_dir", tmp_path / "data"
    make_legacy(legacy)

    assert migrate_legacy_data(legacy, new) is True

    assert (new / "assets" / "products" / "a1.png").is_file()
    assert (new / "backups" / "vmpos_old.db").is_file()
    connection = sqlite3.connect(str(new / "vmpos.db"))
    rows = dict(connection.execute("SELECT name, image_path FROM products"))
    connection.close()
    assert rows["Non"] == "assets/products/a1.png"
    assert rows["Suv"] is None
    # eski papkadagi fayllar o'chirilmagan
    assert (legacy / "vmpos.db").is_file()
    assert not (new / "vmpos.db.kochirilmoqda").exists()


def test_windows_style_absolute_path_is_handled(tmp_path):
    legacy, new = tmp_path / "exe_dir", tmp_path / "data"
    make_legacy(legacy)
    connection = sqlite3.connect(str(legacy / "vmpos.db"))
    connection.execute(
        r"UPDATE products SET image_path = 'C:\VMPOS\assets\products\a1.png' WHERE name='Non'"
    )
    connection.commit()
    connection.close()

    migrate_legacy_data(legacy, new)

    connection = sqlite3.connect(str(new / "vmpos.db"))
    value = connection.execute(
        "SELECT image_path FROM products WHERE name='Non'"
    ).fetchone()[0]
    connection.close()
    assert value == "assets/products/a1.png"


def test_second_run_is_noop_and_never_overwrites_new_data(tmp_path):
    legacy, new = tmp_path / "exe_dir", tmp_path / "data"
    make_legacy(legacy)
    migrate_legacy_data(legacy, new)

    connection = sqlite3.connect(str(new / "vmpos.db"))
    connection.execute("INSERT INTO products (name) VALUES ('Yangi')")
    connection.commit()
    connection.close()

    assert migrate_legacy_data(legacy, new) is False

    connection = sqlite3.connect(str(new / "vmpos.db"))
    count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    connection.close()
    assert count == 3


def test_nothing_to_migrate_when_no_legacy_db(tmp_path):
    assert migrate_legacy_data(tmp_path / "none", tmp_path / "data") is False


def test_same_directory_is_noop(tmp_path):
    make_legacy(tmp_path / "x")
    assert migrate_legacy_data(tmp_path / "x", tmp_path / "x") is False


def test_relative_and_absolute_paths_resolve():
    data = get_data_dir()

    assert resolve_data_path("assets/products/a.png") == data / "assets/products/a.png"
    assert resolve_data_path(str(data / "x.png")) == data / "x.png"
    assert resolve_data_path(None) is None
    assert to_data_relative(data / "assets" / "products" / "a.png") == "assets/products/a.png"
