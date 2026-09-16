"""
Test chuc nang cho DBQueue (module 3).

Kiem tra hang doi trung gian giua handler va DB Writer:
thu tu ghi, an toan khi nhieu thread cung day, va khong lam treo
luong goi khi hang doi rong.

Khong dung toi database that -> chay duoc doc lap, khong can Docker.

Chay:  python -m app.queue.test_queue
"""

import queue
import threading
import time

from app.queue.db_queue import DBQueue, Op, db_queue


def test_thu_tu_fifo():
    """Event lay ra phai dung thu tu da day vao.

    Quan trong voi bang moves: nuoc di thu 5 phai duoc ghi truoc
    nuoc thu 6, neu khong thi khong phat lai duoc van dau.
    """
    q = DBQueue()
    for i in range(5):
        q.put(Op.INSERT_MOVE, {"move_index": i})

    thu_tu = [q.get(timeout=1)["data"]["move_index"] for _ in range(5)]

    assert thu_tu == [0, 1, 2, 3, 4], f"Sai thu tu: {thu_tu}"
    print("[OK] Thu tu FIFO dung:", thu_tu)


def test_dinh_dang_event():
    """Event phai co dung hai truong op va data cho DB Writer doc."""
    q = DBQueue()
    q.put(Op.UPDATE_MATCH_RESULT, {"match_id": 1, "result": "x_win"})

    event = q.get(timeout=1)

    assert event["op"] == Op.UPDATE_MATCH_RESULT
    assert event["data"]["match_id"] == 1
    assert event["data"]["result"] == "x_win"
    print("[OK] Dinh dang event dung:", event)


def test_put_tra_ve_ngay():
    """put() phai tra ve ngay, khong duoc cho database.

    Day la ly do ton tai cua hang doi: handler bo viec vao roi di tiep,
    neu put() cham thi ca server dung hinh voi moi client.
    """
    q = DBQueue()

    bat_dau = time.perf_counter()
    for i in range(1000):
        q.put(Op.INSERT_MOVE, {"move_index": i})
    thoi_gian = time.perf_counter() - bat_dau

    assert thoi_gian < 0.5, f"put() qua cham: {thoi_gian:.3f}s cho 1000 event"
    print(f"[OK] 1000 lan put() mat {thoi_gian * 1000:.1f}ms, khong chan handler")


def test_nhieu_thread_day_song_song():
    """Nhieu luong client cung ghi mot luc khong duoc mat event.

    queue.Queue da thread-safe san nen khong can Lock ben ngoai,
    test nay xac nhan dieu do.
    """
    q = DBQueue()

    def client(ten: str, so_nuoc: int):
        for i in range(so_nuoc):
            q.put(Op.INSERT_MOVE, {"player": ten, "move_index": i})

    threads = [
        threading.Thread(target=client, args=("player_x", 200)),
        threading.Thread(target=client, args=("player_o", 200)),
        threading.Thread(target=client, args=("spectator_log", 100)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert q.size() == 500, f"Mat event, chi con {q.size()}/500"
    print("[OK] 3 thread day song song, nhan du", q.size(), "event")


def test_get_rong_khong_treo():
    """Hang doi rong thi get() raise queue.Empty sau timeout.

    Nho vay DB Writer con dip kiem tra co dung, khong bi ket vinh vien
    khi server tat.
    """
    q = DBQueue()

    bat_dau = time.perf_counter()
    try:
        q.get(timeout=0.3)
        raise AssertionError("Phai raise queue.Empty khi hang doi rong")
    except queue.Empty:
        pass
    thoi_gian = time.perf_counter() - bat_dau

    assert 0.2 < thoi_gian < 1.0, f"Timeout sai: {thoi_gian:.2f}s"
    print(f"[OK] Hang doi rong raise queue.Empty sau {thoi_gian:.2f}s")


def test_join_cho_xu_ly_xong():
    """join() phai cho toi khi moi event da duoc task_done().

    Dung khi tat server: cho DB Writer ghi not roi moi dong ket noi.
    """
    q = DBQueue()
    for i in range(20):
        q.put(Op.INSERT_MOVE, {"move_index": i})

    da_ghi = []

    def writer_gia():
        while True:
            try:
                event = q.get(timeout=0.5)
            except queue.Empty:
                return
            da_ghi.append(event["data"]["move_index"])
            q.task_done()

    t = threading.Thread(target=writer_gia, daemon=True)
    t.start()

    q.join()  # cho toi khi ghi het

    assert len(da_ghi) == 20, f"Chi ghi duoc {len(da_ghi)}/20"
    assert q.size() == 0
    print("[OK] join() cho du", len(da_ghi), "event duoc xu ly xong")


def main():
    print("=" * 58)
    print(" TEST DBQueue - Module 3")
    print("=" * 58)

    test_thu_tu_fifo()
    test_dinh_dang_event()
    test_put_tra_ve_ngay()
    test_nhieu_thread_day_song_song()
    test_get_rong_khong_treo()
    test_join_cho_xu_ly_xong()

    print("=" * 58)
    print(" Tat ca test da qua")
    print(" Instance dung chung san sang, size =", db_queue.size())
    print("=" * 58)


if __name__ == "__main__":
    main()