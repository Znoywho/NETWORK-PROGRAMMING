import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db import BASE

# CREATE TABLE IF NOT EXISTS moves (
#     id          BIGSERIAL    PRIMARY KEY,
#     match_id    VARCHAR(16)  NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
#     player_id   UUID         NOT NULL REFERENCES users(id)   ON DELETE RESTRICT,
#     row_idx     SMALLINT     NOT NULL,
#     col_idx     SMALLINT     NOT NULL,
#     move_index  INTEGER      NOT NULL,
#     created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
#


class moves(BASE):
    __tablename__ = "moves"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"), ondelete="CASCADE")
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), ondelete="RESTRICT")
    cols_idx: Mapped[int] = mapped_column(SmallInteger)
    rows_idx: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
