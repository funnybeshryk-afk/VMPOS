"""Brend belgisini (V harfi + barg) kod orqali chizadi va fayllarni yozadi:

  assets/logo.png       1024x1024 — to'liq ilova ikonkasi (qora yumaloq kvadrat)
  assets/logo.ico       16..256 px — .exe va o'rnatuvchi ikonkasi
  assets/logo_mark.png  512x512, shaffof — faqat belgi, OQ "badge" ustida
                        (chap rels logotipi) uchun: V qora, barg izumrud

Ishga tushirish (loyiha ildizidan):  python packaging/make_icon.py
Pillow kerak (requirements-dev.txt). Ranglar — style.qss palitrasidan.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
SS = 2  # supersampling: chiziqlar silliq chiqishi uchun

EMERALD = (5, 150, 105)
EMERALD_LIGHT = (167, 243, 208)
INK = (28, 25, 23)
WHITE = (255, 255, 255)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def _pts(points):
    return [(x * SS, y * SS) for x, y in points]


def _rotate(points, cx, cy, degrees):
    angle = math.radians(degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    return [
        (
            cx + (x - cx) * cos_a - (y - cy) * sin_a,
            cy + (x - cx) * sin_a + (y - cy) * cos_a,
        )
        for x, y in points
    ]


def _leaf(draw, cx, cy, length, width, degrees, fill, vein):
    top, bottom = [], []

    for i in range(41):
        t = i / 40
        x = -length / 2 + length * t
        half = width / 2 * math.sin(math.pi * t) ** 0.8
        top.append((cx + x, cy - half))
        bottom.append((cx + x, cy + half))

    outline = _rotate(top + bottom[::-1], cx, cy, degrees)
    draw.polygon(_pts(outline), fill=fill)

    stem = _rotate(
        [(cx - length * 0.38, cy), (cx + length * 0.38, cy)], cx, cy, degrees
    )
    draw.line(_pts(stem), fill=vein, width=10 * SS)


def _round_cap(draw, x, y, radius, fill):
    draw.ellipse(
        _pts([(x - radius, y - radius), (x + radius, y + radius)]), fill=fill
    )


def draw_mark(draw, left_color):
    """V (chap chiziq — left_color, o'ng chiziq — izumrud, barg bilan tugaydi)."""

    stroke = 128
    half = stroke / 2

    # chap chiziq
    draw.line(_pts([(268, 300), (500, 742)]), fill=left_color, width=stroke * SS)
    _round_cap(draw, 268, 300, half, left_color)

    # o'ng chiziq — chap ustidan: tekis tutashuv
    draw.line(_pts([(500, 742), (676, 430)]), fill=EMERALD, width=stroke * SS)
    _round_cap(draw, 500, 742, half, EMERALD)

    _leaf(draw, 770, 326, 330, 172, -56, EMERALD, EMERALD_LIGHT)


def render_tile():
    image = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, SIZE * SS - 1, SIZE * SS - 1),
        radius=int(0.225 * SIZE * SS),
        fill=INK,
    )
    draw_mark(draw, WHITE)

    return image.resize((SIZE, SIZE), Image.LANCZOS)


def render_mark():
    """Faqat belgi, shaffof fon, V qora — oq badge ustida ko'rinadi.
    Belgi markazlashtirilgan va atrofida bo'sh joy qoldirilgan."""

    image = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_mark(draw, INK)
    image = image.resize((SIZE, SIZE), Image.LANCZOS)

    bbox = image.getbbox()
    cropped = image.crop(bbox)
    side = int(max(cropped.size) * 1.18)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(
        cropped,
        ((side - cropped.width) // 2, (side - cropped.height) // 2),
        cropped,
    )

    return canvas.resize((512, 512), Image.LANCZOS)


def main():
    ASSETS.mkdir(exist_ok=True)

    tile = render_tile()
    tile.save(ASSETS / "logo.png", optimize=True)
    tile.save(
        ASSETS / "logo.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    render_mark().save(ASSETS / "logo_mark.png", optimize=True)

    print("OK:", ", ".join(sorted(p.name for p in ASSETS.glob("logo*"))))


if __name__ == "__main__":
    main()
