"""
Queue trung gian giua cac coroutine xu ly client va DB Writer.

Nguyen tac: KHONG cho nhieu noi ghi truc tiep vao database cung luc.
Moi request ghi deu di qua hang doi nay, chi mot DB Writer duy nhat
lay ra va ghi tuan tu -> tranh race condition va tranh mat du lieu.

    handler client A  --\\
    handler client B  ----> [ DBQueue ] --> DB Writer --> PostgreSQL
    handler client C  --/

Dung asyncio.Queue (khong phai queue.Queue) vi server chay tren mot
event loop duy nhat: `await queue.get()` nhuong luot cho cac client
khac khi hang doi rong, thay vi chan ca server.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
#  Cac loai thao tac ghi (truong "op" cua event)
# ------------------------------------------------------------
class Op:
    INSERT_USER = "insert_user"
    UPDATE_LAST_LOGIN = "update_last_login"
    INSERT_MATCH = "insert_match"
    UPDATE_MATCH_STATUS = "update_match_status"
    UPDATE_MATCH_RESULT = "update_match_result"
    INSERT_MOVE = "insert_move"


VALID_OPS = {
    value for key, value in vars(Op).items() if not key.startswith("_")
}


# ------------------------------------------------------------
#  Gioi han hang doi
#  Neu database chet, hang doi khong duoc phinh vo han lam het RAM.
#  Yeu cau de bai: thao tac co the cho vo han phai co timeout.
# ------------------------------------------------------------
MAX_QUEUE_SIZE = 1000
PUT_TIMEOUT = 2.0  # giay


class DBQueue:
    """Hang doi ghi database dung chung cho toan server."""

    def __init__(self, maxsize: int = MAX_QUEUE_SIZE):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._dropped = 0  # dem so event bi bo vi hang doi day

    # --------------------------------------------------------
    #  Task 7: ham put() cho cac module khac goi
    # --------------------------------------------------------
    async def put(self, op: str, data: dict[str, Any]) -> bool:
        """
        Day mot request ghi vao hang doi.

        Tra ve True neu day thanh cong, False neu hang doi day.
        KHONG raise exception ra ngoai: mot loi ghi log khong duoc
        lam sap luong xu ly nuoc di cua nguoi choi.
        """
        if op not in VALID_OPS:
            logger.error("Op khong hop le: %s", op)
            return False

        event = {
            "op": op,
            "data": data,
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Cho toi da PUT_TIMEOUT giay. Neu DB Writer dang cham
            # va hang doi day thi bo qua con hon treo ca van dau.
            await asyncio.wait_for(
                self._queue.put(event), timeout=PUT_TIMEOUT
            )
            return True
        except asyncio.TimeoutError:
            self._dropped += 1
            logger.warning(
                "Hang doi day, bo event %s (tong da bo: %d)",
                op, self._dropped,
            )
            return False

    # --------------------------------------------------------
    #  Danh cho DB Writer (task 8) goi
    # --------------------------------------------------------
    async def get(self) -> dict[str, Any]:
        """Lay mot event ra khoi hang doi. Cho neu hang doi rong."""
        return await self._queue.get()

    def task_done(self) -> None:
        """Bao da xu ly xong event vua lay ra."""
        self._queue.task_done()

    async def requeue(self, event: dict[str, Any]) -> bool:
        """
        Day lai event vao hang doi sau khi ghi that bai (task 9 dung).
        Tang retry_count de DB Writer biet da thu bao nhieu lan.
        """
        event["retry_count"] += 1
        try:
            self._queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self._dropped += 1
            logger.error(
                "Khong the requeue event %s, hang doi day", event["op"]
            )
            return False

    # --------------------------------------------------------
    #  Theo doi trang thai, dung cho log va bao cao kiem thu
    # --------------------------------------------------------
    def size(self) -> int:
        return self._queue.qsize()

    def dropped(self) -> int:
        return self._dropped

    def is_empty(self) -> bool:
        return self._queue.empty()

    async def join(self) -> None:
        """Cho toan bo event trong hang doi duoc xu ly xong."""
        await self._queue.join()


# ------------------------------------------------------------
#  Instance dung chung. Cac module khac import cai nay.
#
#  Vi du trong handlers/message.py:
#      from app.queue.db_queue import db_queue, Op
#      await db_queue.put(Op.INSERT_MOVE, {
#          "match_id": room_id,
#          "player_id": player_id,
#          "row_idx": row,
#          "col_idx": col,
#          "move_index": move_number,
#      })
# ------------------------------------------------------------
db_queue = DBQueue()