import json
import logging
import queue
import threading
import time
from pathlib import Path

from sqlalchemy.exc import IntegrityError, OperationalError

from app.db import SessionLocal
from app.models.match import Match
from app.models.move import Move
from app.queue.db_queue import Op, db_queue

logger = logging.getLogger(__name__)

# Lay viec voi timeout thay vi cho vo han, de thread con dip kiem tra
# xem da bi bao dung chua.
POLL_TIMEOUT = 0.5  # giay

# Cho writer ghi not hang doi luc tat server. Rong rai hon POLL_TIMEOUT
# vi buoc ghi not con co the phai thu lai vai lan.
SHUTDOWN_TIMEOUT = 10  # giay

# --- Task 9: xu ly loi ghi database ---------------------------------
# So lan thu lai toi da cho mot event truoc khi bo cuoc.
MAX_RETRIES = 3

# Cho giua cac lan thu, tang dan: 0.5s -> 1s -> 2s.
# Tang dan de neu database dang khoi dong lai thi co thoi gian len,
# ma khong lam thread quay vong lien tuc dot CPU.
RETRY_DELAY_BASE = 0.5

# Event that bai han duoc ghi ra day thay vi bien mat lang le.
# De bai: "du lieu chua truyen hoan tat khong duoc cong nhan la hoan chinh".
DEAD_LETTER_FILE = Path(__file__).resolve().parents[2] / "logs" / "db_failed.jsonl"


class DBWriter(threading.Thread):
    def __init__(self):
        super().__init__(name="db-writer", daemon=True)
        self.queue = db_queue
        self._running = True
        self._session = None
        # Dem de bao cao kiem thu va theo doi suc khoe he thong
        self.stats = {"ok": 0, "retried": 0, "dropped": 0}

    def run(self) -> None:
        logger.info("DB Writer bat dau")
        self._session = SessionLocal()

        while self._running:
            try:
                event = self.queue.get(timeout=POLL_TIMEOUT)
            except queue.Empty:
                continue  # hang doi rong, vong lai kiem tra co dung

            try:
                self._write_with_retry(event)
            except Exception:
                # Lop chan cuoi cung. Dung de mot event hong lam chet
                # ca thread -> se khong con ai ghi database nua.
                logger.exception("Loi ngoai du kien khi xu ly event")
            finally:
                # Luon goi, ke ca khi that bai, de join() khong treo vinh vien.
                self.queue.task_done()

        # Da bi bao dung, nhung hang doi co the con viec: ghi not roi moi di.
        self._drain()
        self._close_session()
        logger.info(
            "DB Writer dung. Thong ke: ghi ok=%d, phai thu lai=%d, bo=%d",
            self.stats["ok"], self.stats["retried"], self.stats["dropped"],
        )

    def stop(self) -> None:
        self._running = False
        if self.is_alive():
            self.join(timeout=SHUTDOWN_TIMEOUT)

    def _drain(self) -> None:
        """Ghi not nhung viec con ket lai trong hang doi truoc khi dung han.

        Vong lap chinh kiem tra `_running` o dau moi nhip, nen khi server
        bao dung no thoat ngay va bo lai moi thu chua lay ra. Do la duong
        mat du lieu lang le nhat: khong loi, khong dead-letter, thong ke
        van bao `dropped=0`. Nen phai vet not o day.
        """
        while True:
            try:
                event = self.queue.get(timeout=0)
            except queue.Empty:
                return

            try:
                self._write_with_retry(event)
            except Exception:
                logger.exception("Loi khi ghi not event luc tat")
            finally:
                self.queue.task_done()

    # ----------------------------------------------------------------
    #  Task 9: vong thu lai
    # ----------------------------------------------------------------
    def _write_with_retry(self, event: dict) -> None:
        """
        Thu ghi event, co thu lai khi loi tam thoi.

        Phan biet hai loai loi:
          - IntegrityError: du lieu sai (danh trung o, move_index trung,
            vi pham khoa ngoai). Thu lai bao nhieu lan cung hong ->
            bo ngay, ghi vao dead-letter.
          - OperationalError: database mat ket noi, dang khoi dong lai,
            het connection. Loi tam thoi -> thu lai co ich.
        """
        op = event["op"]

        for lan in range(1, MAX_RETRIES + 1):
            try:
                self._write(event)
                self.stats["ok"] += 1
                if lan > 1:
                    logger.info("Ghi %s thanh cong o lan thu %d", op, lan)
                return

            except IntegrityError as e:
                # Du lieu vi pham rang buoc -> loi that su, khong thu lai.
                self._session.rollback()
                logger.error(
                    "Du lieu vi pham rang buoc khi ghi %s: %s", op, e.orig
                )
                self._dead_letter(event, f"IntegrityError: {e.orig}")
                self.stats["dropped"] += 1
                return

            except OperationalError as e:
                # Mat ket noi hoac database chua san sang -> thu lai.
                self._session.rollback()
                self.stats["retried"] += 1

                if lan < MAX_RETRIES:
                    cho = RETRY_DELAY_BASE * (2 ** (lan - 1))
                    logger.warning(
                        "Loi ket noi khi ghi %s (lan %d/%d), thu lai sau %.1fs: %s",
                        op, lan, MAX_RETRIES, cho, e.orig,
                    )
                    # Ngu o thread nay khong chan server: handler van
                    # put() vao hang doi binh thuong.
                    time.sleep(cho)
                    self._renew_session()
                else:
                    logger.error(
                        "Ghi %s that bai sau %d lan thu: %s",
                        op, MAX_RETRIES, e.orig,
                    )
                    self._dead_letter(event, f"OperationalError: {e.orig}")
                    self.stats["dropped"] += 1
                    return

            except Exception as e:
                # Loi khong doan truoc -> khong thu lai mu quang.
                self._session.rollback()
                logger.exception("Loi khong xac dinh khi ghi %s", op)
                self._dead_letter(event, f"{type(e).__name__}: {e}")
                self.stats["dropped"] += 1
                return

    def _renew_session(self) -> None:
        """Tao lai session sau khi mat ket noi. Session cu da hong."""
        try:
            self._close_session()
        except Exception:
            pass
        self._session = SessionLocal()

    def _close_session(self) -> None:
        if self._session is not None:
            self._session.close()
        SessionLocal.remove()  # scoped_session giu session theo tung thread
        self._session = None

    def _dead_letter(self, event: dict, ly_do: str) -> None:
        """
        Ghi event khong luu duoc ra file de con truy lai sau.

        Mat du lieu lang le la dieu te nhat: van dau se thieu nuoc di
        ma khong ai biet. Ghi ra day de con doi chieu khi kiem thu.
        """
        try:
            DEAD_LETTER_FILE.parent.mkdir(parents=True, exist_ok=True)
            ban_ghi = {
                "thoi_diem": time.strftime("%Y-%m-%d %H:%M:%S"),
                "op": event["op"],
                "data": event["data"],
                "ly_do": ly_do,
            }
            with DEAD_LETTER_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ban_ghi, ensure_ascii=False, default=str) + "\n")
        except Exception:
            # Ghi dead-letter that bai cung khong duoc lam chet writer.
            logger.exception("Khong ghi duoc dead-letter")

    # ----------------------------------------------------------------
    #  Ghi that xuong database
    # ----------------------------------------------------------------
    def _write(self, event: dict) -> None:
        op = event["op"]
        data = event["data"]

        if op == Op.INSERT_MOVE:
            self._session.add(
                Move(
                    match_id=_as_int(data["match_id"]),
                    player_id=_as_int(data["player_id"]),
                    row_idx=data["row_idx"],
                    col_idx=data["col_idx"],
                    move_index=data["move_index"],
                )
            )

        elif op == Op.UPDATE_MATCH_RESULT:
            self._session.query(Match).filter(
                Match.id == _as_int(data["match_id"])
            ).update(
                {
                    Match.status: data["status"],
                    Match.result: data["result"],
                    Match.winner_id: _as_int(data["winner_id"]),
                    Match.ended_at: data["ended_at"],
                },
                synchronize_session=False,
            )

        else:
            # Raise chu khong return: nhanh `except Exception` ben
            # _write_with_retry moi dem duoc la `dropped` va luu vao
            # dead-letter. Return lang le se bi tinh nham la ghi thanh cong.
            raise ValueError(f"Khong biet op: {op}")

        self._session.commit()


def _as_int(value):
    return int(value) if value is not None else None