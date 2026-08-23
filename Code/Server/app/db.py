from sqlalchemy import create_engine

from sqlalchemy.orm import scoped_session, sessionmaker
from config import Config
from sqlalchemy.orm import declarative_base

BASE = declarative_base()
DATABASE_URL = Config.DATABASE_URI

print("run engine")
engine = create_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True, # auto reconnect
        pool_recycle=1800   #recycle connect after 30 minutes
        )
print("run session local")

SessionLocal = scoped_session(sessionmaker(bind=engine))

def init_db():
    print("initialize database")
    BASE.metadata.create_all(bind = engine) 


