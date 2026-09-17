from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import BASE



class Match(BASE):
    __tablename__ = "matches"

    # BIGSERIAL do Postgres cap. Hang nay duoc INSERT dong bo ngay luc mo
    # phong, roi id tra ve chinh la room_id ben RoomManager.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    player_x_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    player_o_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="waiting")
    result: Mapped[str | None] = mapped_column(String(16), nullable=True)
    winner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    board_rows: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=15)
    board_cols: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=15)
    win_condition: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Match {self.id} status={self.status} result={self.result}>"
