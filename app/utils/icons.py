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


def load_checkable_icon(name, unchecked_color, checked_color, size=24):
    """Checkable tugma uchun ikki holatli (On/Off) QIcon.

    QAbstractButton checkable bo'lsa, checked holatga o'tganda
    QIcon.On pixmap'ni, aks holda QIcon.Off'ni o'zi avtomatik
    tanlaydi — alohida signal ulashning hojati yo'q (CategoryBar va
    SidebarMenu shu bitta funksiyadan foydalanadi).
    """

    icon = QIcon()

    icon.addPixmap(
        load_icon(name, color=unchecked_color, size=size).pixmap(
            QSize(size, size)
        ),
        QIcon.Normal,
        QIcon.Off,
    )
    icon.addPixmap(
        load_icon(name, color=checked_color, size=size).pixmap(
            QSize(size, size)
        ),
        QIcon.Normal,
        QIcon.On,
    )

    return icon
