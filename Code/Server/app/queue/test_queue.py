"""
Test chuc nang cho DBQueue (module 3, task 6-7).

Chay:  python -m app.queue.test_queue
"""

import threading
import time

from app.queue.db_queue import DBQueue, Op, db_queue


def test_thu_tu_fifo():
    """Event lay ra phai dung thu tu da day vao."""
    q = DBQueue()
    for i in range(5):
        q.put(Op.INSERT_MOVE, {"move_index": i})

    thu_tu = []
    for _ in range(5):
        event = q.get(timeout=1)
        thu_tu.append(event["data"]["move_index"])
        q.task_done()

    assert thu_tu == [0, 1, 2, 3, 4], f"Sai thu tu: {thu_tu}"
    print("[OK] Thu tu FIFO dung:", thu_tu)


def test_op_khong_hop_le():
    """Op la khong duoc vao hang doi."""
    q = DBQueue()
    ket_qua = q.put("xoa_het_database", {})
    assert ket_qua is False
    assert q.size() == 0
    print("[OK] Da chan op khong hop le")


def test_nhieu_thread_day_song_song():
    """Mo phong nhieu client tren cac thread khac nhau cung ghi."""
    q = DBQueue()

    def client(ten: str, so_nuoc: int):
        for i in range(so_nuoc):
            q.put(Op.INSERT_MOVE, {"player": ten, "move_index": i})

    threads = [
        threading.Thread(target=client, args=("player_x", 50)),
        threading.Thread(target=client, args=("player_o", 50)),
        threading.Thread(target=client, args=("spectator_log", 30)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert q.size() == 130, f"Thieu event, chi co {q.size()}"
    print("[OK] 3 thread day song song, nhan du", q.size(), "event")


def test_requeue():
    """Event ghi that bai duoc day lai voi retry_count tang."""
    q = DBQueue()
    q.put(Op.INSERT_MATCH, {"id": "abc123"})

    event = q.get(timeout=1)
    assert event["retry_count"] == 0

    q.requeue(event)
    event_lai = q.get(timeout=1)
    assert event_lai["retry_count"] == 1
    print("[OK] Requeue hoat dong, retry_count =", event_lai["retry_count"])


def test_get_rong_tra_None():
    """Hang doi rong thi get() tra None sau timeout, khong treo."""
    q = DBQueue()
    bat_dau = time.time()
    ket_qua = q.get(timeout=0.3)
    thoi_gian = time.time() - bat_dau

    assert ket_qua is None
    assert 0.2 < thoi_gian < 1.0, f"Timeout sai: {thoi_gian:.2f}s"
    print(f"[OK] Hang doi rong tra None sau {thoi_gian:.2f}s, khong treo")


def test_hang_doi_day():
    """Hang doi day thi bo event, khong treo server."""
    q = DBQueue(maxsize=3)
    for i in range(3):
        q.put(Op.INSERT_MOVE, {"move_index": i})

    print("     Hang doi da day, thu day them (cho ~2 giay)...")
    ket_qua = q.put(Op.INSERT_MOVE, {"move_index": 99})

    assert ket_qua is False
    assert q.dropped() == 1
    print("[OK] Bo event khi day, so event da bo:", q.dropped())


def main():
    print("=" * 55)
    print(" TEST DBQueue - Module 3 Task 6, 7")
    print("=" * 55)

    test_thu_tu_fifo()
    test_op_khong_hop_le()
    test_nhieu_thread_day_song_song()
    test_requeue()
    test_get_rong_tra_None()
    test_hang_doi_day()

    print("=" * 50)
    print(" Tat ca test da qua")
    print(" Instance dung chung san sang, size =", db_queue.size())
    print("=" * 50)


if __name__ == "__main__":
    main()