from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.paths import get_app_base_dir

# Avval "app/database/vmpos.db" — joriy ish papkasiga (CWD) nisbatan
# edi. .exe sifatida yig'ilganda bu ishonchsiz (CWD ishga tushirish
# usuliga qarab har xil bo'lishi mumkin) va, eng yomoni, baza build
# paketi ichida qolib ketardi — qayta yig'ilganda yo'qolardi. Endi
# get_app_base_dir() orqali doim EXE/skript joylashgan papkaga
# nisbatan aniqlanadi.
DATABASE_PATH = get_app_base_dir() / "vmpos.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)