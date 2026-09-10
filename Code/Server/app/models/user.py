import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import BASE

# CREATE TABLE IF NOT EXISTS users (
#     id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
#     username        VARCHAR(32)  NOT NULL UNIQUE,
#     password_hash   VARCHAR(255),
#     created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
#     last_login_at   TIMESTAMPTZ,
#
#     CONSTRAINT chk_users_username_len CHECK (char_length(username) >= 3)
# );


class User(BASE):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
            UUID(as_uuid=True), 
            primary_key=True, 
            server_default=text("gen_random_uuid()"))
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    last_login_at: Mapped[datetime] = mapped_column(DateTime)
