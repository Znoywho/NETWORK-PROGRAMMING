"""
Test DBQueue.

Chay:  python -m app.queue.test_queue
"""

import threading

from app.queue.db_queue import DBQueue, Op, db_queue


def test_put_va_get():
    """Bo mot viec vao roi lay ra thi phai con nguyen."""
    q = DBQueue()
    q.put(Op.INSERT_MOVE, {"row_idx": 3, "col_idx": 7})

    viec = q.get()
    assert viec["op"] == Op.INSERT_MOVE
    assert viec["data"] == {"row_idx": 3, "col_idx": 7}
    q.task_done()
    print("[OK] put/get giu nguyen noi dung")


def test_thu_tu_fifo():
    """Lay ra phai dung thu tu da bo vao.

    Cac nuoc di phai xuong DB theo dung thu tu danh, va UPDATE_MATCH_RESULT
    phai la viec cuoi cung — khong thi lich su doc ra se thay van ket thuc
    truoc khi co du nuoc di.
    """
    q = DBQueue()
    for i in range(1, 4):
        q.put(Op.INSERT_MOVE, {"move_index": i})
    q.put(Op.UPDATE_MATCH_RESULT, {"match_id": 1})

    thu_tu = []
    for _ in range(4):
        thu_tu.append(q.get()["op"])
        q.task_done()

    assert thu_tu == [Op.INSERT_MOVE, Op.INSERT_MOVE, Op.INSERT_MOVE, Op.UPDATE_MATCH_RESULT]
    print("[OK] FIFO dung, UPDATE_MATCH_RESULT di cuoi")


def test_nhieu_thread_cung_day():
    """Nhieu client ghi mot luc thi khong duoc mat viec nao."""
    q = DBQueue()

    def client(ten, so_nuoc):
        for i in range(so_nuoc):
            q.put(Op.INSERT_MOVE, {"player": ten, "move_index": i})

    threads = [
        threading.Thread(target=client, args=("player_x", 10)),
        threading.Thread(target=client, args=("player_o", 10)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert q.size() == 20, f"Thieu viec, chi con {q.size()}"
    print("[OK] 2 thread day song song, nhan du", q.size(), "viec")


def test_join_cho_ghi_xong():
    """join() phai cho toi khi moi viec deu task_done()."""
    q = DBQueue()
    for i in range(5):
        q.put(Op.INSERT_MOVE, {"move_index": i})

    def writer_gia():
        for _ in range(5):
            q.get()
            q.task_done()

    threading.Thread(target=writer_gia).start()
    q.join()  # chan o day cho toi khi writer gia xu ly het
    assert q.size() == 0
    print("[OK] join() cho den khi hang doi sach")


def main():
    print("=" * 50)
    print(" TEST DBQueue")
    print("=" * 50)

    test_put_va_get()
    test_thu_tu_fifo()
    test_nhieu_thread_cung_day()
    test_join_cho_ghi_xong()

    print("=" * 50)
    print(" Tat ca test da qua")
    print(" Instance dung chung san sang, size =", db_queue.size())
    print("=" * 50)


if __name__ == "__main__":
    main()
