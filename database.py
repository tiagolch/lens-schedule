from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = "lensagenda.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()