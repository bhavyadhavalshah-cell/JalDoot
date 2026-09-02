import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Fast engine initialization with performance pragmas
engine = None
try:
    if settings.DATABASE_URL.startswith("postgresql"):
        temp_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
        logger.info(f"Connected successfully to PostgreSQL database at {settings.DATABASE_URL}")
    else:
        engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite at {settings.SQLITE_FALLBACK_URL}")
    engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

# SQLite WAL mode & memory cache performance booster
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
    except Exception:
        pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
