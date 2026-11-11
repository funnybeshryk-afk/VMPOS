from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.paths import get_database_path

# Avval "app/database/vmpos.db" — joriy ish papkasiga (CWD) nisbatan
# edi. .exe sifatida yig'ilganda bu ishonchsiz (CWD ishga tushirish
# usuliga qarab har xil bo'lishi mumkin) va, eng yomoni, baza build
# paketi ichida qolib ketardi — qayta yig'ilganda yo'qolardi. Endi
# get_data_dir() orqali dastur papkasidan ALOHIDA doimiy papkada
# turadi (.exe rejimida %LOCALAPPDATA%\VMPOS) — yangilashda yo'qolmaydi.
DATABASE_PATH = get_database_path()
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