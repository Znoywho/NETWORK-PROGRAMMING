"""
Hang doi ghi database.

Y tuong: handler KHONG ghi thang xuong DB. No bo mot "viec can ghi" vao
hang doi roi di tiep ngay. Mot luong DB Writer duy nhat lay tung viec ra ghi.

    handler  --put()-->  [ DBQueue ]  --get()-->  DB Writer  -->  PostgreSQL

Vi sao can: server chay tren MOT vong lap selectors duy nhat
(app/network/server.py). Neu handler ngoi cho DB commit thi ca server
dung hinh voi moi client, chu khong rieng nguoi vua danh.

Dung queue.Queue cua thu vien chuan: no da thread-safe san, nen luong
chinh va luong db-writer dung chung mot instance duoc.
"""

import queue


class Op:
    INSERT_MOVE = "insert_move"
    UPDATE_MATCH_RESULT = "update_match_result"


class DBQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, op: str, data: dict) -> None:
        """Handler goi ham nay. Tra ve ngay, khong cho database."""
        self._queue.put({"op": op, "data": data})

    def get(self, timeout: float | None = None) -> dict:
        """DB Writer goi ham nay. Raise queue.Empty neu het `timeout` giay."""
        return self._queue.get(timeout=timeout)

    def task_done(self) -> None:
        """Bao da ghi xong viec vua lay ra (de join() biet luc nao xong)."""
        self._queue.task_done()

    def size(self) -> int:
        return self._queue.qsize()

    def join(self) -> None:
        """Cho toi khi moi viec trong hang doi da duoc ghi xong."""
        self._queue.join()


# Instance dung chung cho toan server.
db_queue = DBQueue()
