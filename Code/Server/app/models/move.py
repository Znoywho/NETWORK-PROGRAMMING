from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import BASE

# Anh xa 1-1 voi bang `moves` trong migrations/init.sql.
# Ten cot la row_idx/col_idx chu khong phai row/col vi ROW la tu khoa SQL.
# Hai UNIQUE constraint ben SQL chan ghi trung:
#   - (match_id, move_index)          : khong co hai nuoc cung so thu tu
#   - (match_id, row_idx, col_idx)    : khong danh hai lan cung mot o


class Move(BASE):
    __tablename__ = "moves"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    match_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    row_idx: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    col_idx: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # Bat dau tu 1. So le = luot X, so chan = luot O.
    move_index: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<Move {self.match_id}#{self.move_index} ({self.row_idx},{self.col_idx})>"
