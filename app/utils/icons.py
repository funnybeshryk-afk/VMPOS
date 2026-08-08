from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "feather"
)


@lru_cache(maxsize=None)
def _load_template(name):
    return (_ICONS_DIR / f"{name}.svg").read_text(encoding="utf-8")


def load_icon(name, color="#334155", size=24):
    """Feather ikonkasini kerakli rangda qaytaradi.

    Manba SVG fayllari bitta shablon (stroke="currentColor") —
    Qt buni CSS'dagi kabi avtomatik almashtirmaydi, shuning uchun
    matnda o'zimiz almashtirib, natijani QPixmap'ga chizamiz.
    Har bir tugma o'z rangida (oq, kulrang va h.k.) ishlatishi mumkin,
    lekin fayl bitta — ranglar aralashib ketmaydi.
    """

    svg_data = _load_template(name).replace("currentColor", color)

    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)

    renderer = QSvgRenderer(svg_data.encode("utf-8"))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
