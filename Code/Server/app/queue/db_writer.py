
import logging
import queue
import threading

from app.db import SessionLocal
from app.models.match import Match
from app.models.move import Move
from app.queue.db_queue import Op, db_queue

logger = logging.getLogger(__name__)

# Lay viec voi timeout thay vi cho vo han, de thread con dip kiem tra
# xem da bi bao dung chua.
POLL_TIMEOUT = 0.5  # giay


def _as_int(value):
    return int(value) if value is not None else None


class DBWriter(threading.Thread):
    def __init__(self):
        super().__init__(name="db-writer", daemon=True)
        self.queue = db_queue
        self._running = True

    def run(self) -> None:
        logger.info("DB Writer bat dau")
        session = SessionLocal()
        while self._running:
            try:
                event = self.queue.get(timeout=POLL_TIMEOUT)
            except queue.Empty:
                continue  # hang doi rong, vong lai kiem tra co dung
            self._write(session, event)
            self.queue.task_done()
        session.close()
        SessionLocal.remove()  # scoped_session giu session theo tung thread
        logger.info("DB Writer dung")

    def stop(self) -> None:
        self._running = False
        if self.is_alive():
            self.join(timeout=5)

    def _write(self, session, event: dict) -> None:
        op = event["op"]
        data = event["data"]
        try:
            if op == Op.INSERT_MOVE:
                session.add(
                    Move(
                        match_id=_as_int(data["match_id"]),
                        player_id=_as_int(data["player_id"]),
                        row_idx=data["row_idx"],
                        col_idx=data["col_idx"],
                        move_index=data["move_index"],
                    )
                )

            elif op == Op.UPDATE_MATCH_RESULT:
                session.query(Match).filter(Match.id == _as_int(data["match_id"])).update(
                    {
                        Match.status: data["status"],
                        Match.result: data["result"],
                        Match.winner_id: _as_int(data["winner_id"]),
                        Match.ended_at: data["ended_at"],
                    },
                    synchronize_session=False,
                )

            else:
                logger.error("Khong biet op %s, bo qua", op)
                return

            session.commit()

        except Exception:
            session.rollback()
            logger.exception("Ghi that bai, bo qua event %s", op)
