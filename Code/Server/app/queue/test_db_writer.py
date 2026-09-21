"""
Test xu ly loi ghi database (module 3, task 9).

Dung session gia lap de mo phong cac tinh huong loi ma khong can
database that -> chay doc lap, khong can Docker.

Chay:  python -m app.queue.test_db_writer
"""

import time

from sqlalchemy.exc import IntegrityError, OperationalError

from app.queue import db_writer
from app.queue.db_queue import DBQueue, Op
from app.queue.db_writer import DBWriter, MAX_RETRIES


class SessionGia:
    """Session gia lap: dem so lan commit va nem loi theo kich ban."""

    def __init__(self, loi_theo_lan=None, tre=0.0):
        # loi_theo_lan: dict {so_lan_commit: exception_de_nem}
        self.loi_theo_lan = loi_theo_lan or {}
        # tre: moi lan commit ton bao nhieu giay (gia lap DB that)
        self.tre = tre
        self.so_lan_commit = 0
        self.so_lan_rollback = 0

    def add(self, obj):
        pass

    def query(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def update(self, *a, **kw):
        pass

    def commit(self):
        self.so_lan_commit += 1
        if self.tre:
            time.sleep(self.tre)
        loi = self.loi_theo_lan.get(self.so_lan_commit)
        if loi:
            raise loi

    def rollback(self):
        self.so_lan_rollback += 1

    def close(self):
        pass


def _writer_voi_session(session):
    """Tao DBWriter khong chay thread, gan san session gia."""
    w = DBWriter()
    w._session = session
    w._renew_session = lambda: None  # khong tao session that
    return w


def _writer_chay_that(session):
    """Writer chay thread that, nhung SessionLocal tra ve session gia."""
    db_writer.SessionLocal = lambda: session
    w = DBWriter()
    w._renew_session = lambda: None
    w._close_session = lambda: None
    w.queue = DBQueue()  # hang doi rieng, khong dung chung voi server
    return w


def _loi_ket_noi():
    return OperationalError("SELECT 1", {}, Exception("connection closed"))


def _loi_rang_buoc():
    return IntegrityError("INSERT", {}, Exception("duplicate key"))


EVENT_MOVE = {
    "op": Op.INSERT_MOVE,
    "data": {
        "match_id": 1, "player_id": 1,
        "row_idx": 7, "col_idx": 7, "move_index": 1,
    },
}


def test_ghi_thanh_cong_khong_thu_lai():
    """Ghi tron tru thi chi commit dung mot lan."""
    s = SessionGia()
    w = _writer_voi_session(s)

    w._write_with_retry(EVENT_MOVE)

    assert s.so_lan_commit == 1
    assert w.stats["ok"] == 1
    assert w.stats["retried"] == 0
    print("[OK] Ghi thanh cong lan dau, khong thu lai")


def test_loi_ket_noi_thu_lai_roi_thanh_cong():
    """Mat ket noi lan dau, lan hai ghi duoc -> khong mat du lieu."""
    s = SessionGia(loi_theo_lan={1: _loi_ket_noi()})
    w = _writer_voi_session(s)

    w._write_with_retry(EVENT_MOVE)

    assert s.so_lan_commit == 2, f"Phai commit 2 lan, thuc te {s.so_lan_commit}"
    assert s.so_lan_rollback == 1
    assert w.stats["ok"] == 1
    assert w.stats["dropped"] == 0
    print("[OK] Mat ket noi lan 1, thu lai lan 2 thanh cong")


def test_loi_ket_noi_lien_tuc_bo_sau_max_retries():
    """Database chet han -> thu du MAX_RETRIES lan roi bo, khong lap vo han."""
    loi = {i: _loi_ket_noi() for i in range(1, MAX_RETRIES + 1)}
    s = SessionGia(loi_theo_lan=loi)
    w = _writer_voi_session(s)

    bat_dau = time.perf_counter()
    w._write_with_retry(EVENT_MOVE)
    thoi_gian = time.perf_counter() - bat_dau

    assert s.so_lan_commit == MAX_RETRIES
    assert w.stats["dropped"] == 1
    assert w.stats["ok"] == 0
    # Cho tang dan 0.5 + 1.0 = 1.5s giua 3 lan thu
    assert thoi_gian > 1.0, f"Khong thay cho giua cac lan thu: {thoi_gian:.2f}s"
    print(f"[OK] Thu du {MAX_RETRIES} lan trong {thoi_gian:.1f}s roi bo cuoc")


def test_vi_pham_rang_buoc_khong_thu_lai():
    """Du lieu sai thi thu lai vo nghia -> phai bo ngay lan dau."""
    loi = {i: _loi_rang_buoc() for i in range(1, 10)}
    s = SessionGia(loi_theo_lan=loi)
    w = _writer_voi_session(s)

    w._write_with_retry(EVENT_MOVE)

    assert s.so_lan_commit == 1, "Vi pham rang buoc khong duoc thu lai"
    assert w.stats["dropped"] == 1
    assert w.stats["retried"] == 0
    print("[OK] Vi pham rang buoc bo ngay, khong thu lai vo ich")


def test_loi_khong_lam_chet_writer():
    """Sau mot event hong, writer van ghi duoc event tiep theo."""
    s = SessionGia(loi_theo_lan={1: _loi_rang_buoc()})
    w = _writer_voi_session(s)

    w._write_with_retry(EVENT_MOVE)   # event hong
    w._write_with_retry(EVENT_MOVE)   # event tiep theo

    assert w.stats["dropped"] == 1
    assert w.stats["ok"] == 1, "Writer phai tiep tuc lam viec sau loi"
    print("[OK] Mot event hong khong lam chet writer")


def test_op_la_bi_bo_vao_dead_letter():
    """Op khong ai biet phai duoc dem la bo, khong duoc tinh la ghi xong.

    Truoc day nhanh nay chi log roi return, nen ham goi tuong la
    thanh cong: event bien mat ma thong ke van bao ok.
    """
    s = SessionGia()
    w = _writer_voi_session(s)
    da_luu = []
    w._dead_letter = lambda event, ly_do: da_luu.append(ly_do)

    w._write_with_retry({"op": "insert_moves", "data": {"match_id": 1}})

    assert s.so_lan_commit == 0, "Op la thi khong duoc commit gi ca"
    assert w.stats["ok"] == 0, "Khong ghi gi ma bao ok la sai"
    assert w.stats["dropped"] == 1
    assert len(da_luu) == 1, "Event phai duoc luu vao dead-letter"
    print("[OK] Op la bi bo vao dead-letter, khong tinh la ghi thanh cong")


def test_tat_server_van_ghi_not_hang_doi():
    """Tat server luc hang doi con viec thi khong duoc mat nuoc di.

    Vong lap chinh kiem tra co dung o dau moi nhip nen no thoat ngay,
    bo lai moi thu chua lay ra. Mat kieu nay khong sinh loi, khong vao
    dead-letter, thong ke van bao dropped=0 -> phai co test rieng.
    """
    s = SessionGia(tre=0.02)  # moi nuoc di ton 20ms de ghi
    w = _writer_chay_that(s)

    for i in range(1, 21):
        w.queue.put(
            Op.INSERT_MOVE,
            {"match_id": 1, "player_id": 1,
             "row_idx": i, "col_idx": i, "move_index": i},
        )

    w.start()
    time.sleep(0.1)  # writer moi kip ghi vai nuoc dau
    assert w.queue.size() > 0, "Test vo nghia neu hang doi da kip rong"

    w.stop()  # giong luc nhan Ctrl+C o server

    assert w.queue.size() == 0, f"Con {w.queue.size()} event ket trong hang doi"
    assert s.so_lan_commit == 20, f"Chi ghi duoc {s.so_lan_commit}/20 nuoc di"
    assert w.stats["ok"] == 20
    print("[OK] Tat server van ghi not du", s.so_lan_commit, "nuoc di")


def main():
    print("=" * 58)
    print(" TEST xu ly loi ghi DB - Module 3 Task 9")
    print("=" * 58)

    test_ghi_thanh_cong_khong_thu_lai()
    test_loi_ket_noi_thu_lai_roi_thanh_cong()
    test_vi_pham_rang_buoc_khong_thu_lai()
    test_loi_khong_lam_chet_writer()
    test_loi_ket_noi_lien_tuc_bo_sau_max_retries()
    test_op_la_bi_bo_vao_dead_letter()
    test_tat_server_van_ghi_not_hang_doi()

    print("=" * 58)
    print(" Tat ca test da qua")
    print("=" * 58)


if __name__ == "__main__":
    main()