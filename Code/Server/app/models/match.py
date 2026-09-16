import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import BASE


# CREATE TABLE IF NOT EXISTS matches (
#     id              VARCHAR(16)  PRIMARY KEY,
#     player_x_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
#     player_o_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
#     status          VARCHAR(16)  NOT NULL DEFAULT 'waiting',
#     result          VARCHAR(16),
#     winner_id       UUID                  REFERENCES users(id) ON DELETE SET NULL,
#     board_rows      SMALLINT     NOT NULL DEFAULT 15,
#     board_cols      SMALLINT     NOT NULL DEFAULT 15,
#     win_condition   SMALLINT     NOT NULL DEFAULT 5,
#     created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
#     started_at      TIMESTAMPTZ,
#     ended_at        TIMESTAMPTZ,
#
#     -- Hai nguoi choi phai khac nhau
#     CONSTRAINT chk_matches_diff_players
#         CHECK (player_x_id <> player_o_id),
#
#     -- Trang thai khop voi RoomStatus ben module 4
#     CONSTRAINT chk_matches_status
#         CHECK (status IN ('waiting', 'playing', 'finished', 'aborted')),
#
#     -- Ket qua khop voi message game_result
#     CONSTRAINT chk_matches_result
#         CHECK (result IS NULL OR result IN ('x_win', 'o_win', 'draw', 'aborted')),
#
#     -- Van da ket thuc thi bat buoc phai co ket qua va thoi diem ket thuc
#     CONSTRAINT chk_matches_finished_has_result
#         CHECK (status <> 'finished' OR (result IS NOT NULL AND ended_at IS NOT NULL)),
#
#     -- Hoa hoac huy thi khong duoc co nguoi thang
#     CONSTRAINT chk_matches_winner_consistency
#         CHECK (result IS NULL OR result IN ('draw', 'aborted') OR winner_id IS NOT NULL),
#
#     CONSTRAINT chk_matches_time_order
#         CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at)
# );

class Matches(BASE):
    __tablename__ = "matches"
    id: Mapped[uuid.UUID] = mapped_column(
           UUID(as_uuid = True),
           primary_key=True,
           autoincrement=True
        )
    player_x_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    player_o_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16), default="Waiting")  
    winner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), ondelete = "CASCADE")
    board_cols: Mapped[int] = mapped_column(SmallInteger)
    board_rows: Mapped[int] = mapped_column(SmallInteger)
    win_condition: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime] = mapped_column(DateTime)






#     player_x_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
#     player_o_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
#     status          VARCHAR(16)  NOT NULL DEFAULT 'waiting',
#     result          VARCHAR(16),
#     winner_id       UUID                  REFERENCES users(id) ON DELETE SET NULL,
#     board_rows      SMALLINT     NOT NULL DEFAULT 15,
#     board_cols      SMALLINT     NOT NULL DEFAULT 15,
#     win_condition   SMALLINT     NOT NULL DEFAULT 5,
#     created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
#     started_at      TIMESTAMPTZ,
#     ended_at        TIMESTAMPTZ,

