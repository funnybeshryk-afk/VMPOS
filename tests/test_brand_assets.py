from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def test_icon_has_all_windows_sizes():
    sizes = set(Image.open(ASSETS / "logo.ico").info["sizes"])

    assert {(16, 16), (32, 32), (48, 48), (256, 256)} <= sizes


def test_tile_is_square_with_transparent_corners():
    tile = Image.open(ASSETS / "logo.png").convert("RGBA")

    assert tile.size[0] == tile.size[1] >= 512
    assert tile.getpixel((0, 0))[3] == 0          # yumaloq угол — shaffof
    assert tile.getpixel((tile.width // 2, 10))[3] == 255


def test_mark_is_transparent_and_not_empty():
    mark = Image.open(ASSETS / "logo_mark.png").convert("RGBA")

    assert mark.getpixel((0, 0))[3] == 0
    assert mark.getbbox() is not None


def test_generator_output_matches_committed_assets(tmp_path, monkeypatch):
    """Ikonka kod bilan chiziladi — repodagi fayllar generator bilan
    sinxron bo'lishi kerak (qo'lda tahrirlanib qolmasin)."""

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "make_icon", ASSETS.parent / "packaging" / "make_icon.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fresh = module.render_tile().convert("RGBA")
    committed = Image.open(ASSETS / "logo.png").convert("RGBA")

    assert fresh.size == committed.size
    assert list(fresh.getdata()) == list(committed.getdata())
