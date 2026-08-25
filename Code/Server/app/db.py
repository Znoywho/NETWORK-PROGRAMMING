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

SessionLocal = scoped_session(sessionmaker(bind=engine))# Create Thread safety 

session = SessionLocal # Create new session (thread)

def init_db():
    print("initialize database")
    BASE.metadata.create_all(bind=engine)  # Denpendency tracking: create `table` in the exact model

# EXAMPLE:
#     from sqlalchemy import create_engine
#     from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
#
# # 1. Define the declarative base class
#     class Base(DeclarativeBase):
#         pass
#
# # 2. Define your ORM models inheriting from the Base
#     class User(Base):
#         __tablename__ = "users"
#
#         id: Mapped[int] = mapped_column(primary_key=True)
#         name: Mapped[str]
#
# # 3. Create a database connection engine
#     engine = create_engine("sqlite:///example.db")
#
# # 4. Generate all tables in the database
#     Base.metadata.create_all(engine)
