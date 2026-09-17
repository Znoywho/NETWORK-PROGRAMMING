"""
Test xu ly loi ghi database (module 3, task 9).

Dung session gia lap de mo phong cac tinh huong loi ma khong can
database that -> chay doc lap, khong can Docker.

Chay:  python -m app.queue.test_db_writer
"""

import time

from sqlalchemy.exc import IntegrityError, OperationalError

from app.queue.db_queue import Op
from app.queue.db_writer import DBWriter, MAX_RETRIES


class SessionGia:
    """Session gia lap: dem so lan commit va nem loi theo kich ban."""

    def __init__(self, loi_theo_lan=None):
        # loi_theo_lan: dict {so_lan_commit: exception_de_nem}
        self.loi_theo_lan = loi_theo_lan or {}
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


def main():
    print("=" * 58)
    print(" TEST xu ly loi ghi DB - Module 3 Task 9")
    print("=" * 58)

    test_ghi_thanh_cong_khong_thu_lai()
    test_loi_ket_noi_thu_lai_roi_thanh_cong()
    test_vi_pham_rang_buoc_khong_thu_lai()
    test_loi_khong_lam_chet_writer()
    test_loi_ket_noi_lien_tuc_bo_sau_max_retries()

    print("=" * 58)
    print(" Tat ca test da qua")
    print("=" * 58)


if __name__ == "__main__":
    main()