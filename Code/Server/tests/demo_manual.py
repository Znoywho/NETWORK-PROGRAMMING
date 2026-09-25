"""Bảng điều khiển tay cho hai player bot: bạn gõ lệnh, bot làm theo.

Chạy: python -m tests.demo_manual
Gõ `help` để xem danh sách lệnh.

Khác với demo_live_match (chạy một mạch rồi tự kiểm tra), file này để trình
bày trực tiếp: mọi bản tin server gửi về đều in ra ngay khi tới, kể cả lúc
bạn đang ngồi chờ hết 60 giây reconnect.
"""

import select
import sys
from typing import Any
from uuid import uuid4

from tests.demo_live_match import (
    DEMO_PASSWORD,
    DemoError,
    TcpDemoClient,
    _message_details,
    _state_move_count,
)


HOST = "127.0.0.1"
PORT = 8765

# Ván mẫu: X ăn hàng ngang trên cùng, O chặn hụt ở hàng dưới.
SCRIPT = [
    ("x", 0, 0), ("o", 1, 0),
    ("x", 0, 1), ("o", 1, 1),
    ("x", 0, 2), ("o", 1, 2),
    ("x", 0, 3), ("o", 1, 3),
    ("x", 0, 4),
]

HELP = """
  login            tao 2 tai khoan demo moi va dang nhap ca hai bot X, O
  invite           X gui loi moi cho O
  accept / reject  O tra loi loi moi dang cho
  move <x|o> r c   cho mot bot danh vao o (r, c), vi du: move x 7 8
  auto [n]         danh theo van mau; n = so nuoc, bo trong = danh het
  disconnect <x|o> dong TCP socket cua bot do (gia lap rot mang)
  reconnect <x|o>  mo socket moi va dang nhap lai bang chinh tai khoan do
  board            in ban co hien tai theo game_state moi nhat
  players          hoi server danh sach nguoi choi online
  wait [giay]      chi ngoi nghe server (mac dinh 5s) — de xem het gio
  help             in bang nay
  quit             dong ca hai bot va thoat
"""


class Console:
    def __init__(self) -> None:
        self.bots: dict[str, TcpDemoClient | None] = {"x": None, "o": None}
        self.ids: dict[str, str] = {}
        self.usernames: dict[str, str] = {}
        self.room_id: str | None = None
        self.invite_id: str | None = None
        self.board: list[list[int]] | None = None
        self.finished = False

    # --- nhận bản tin -------------------------------------------------
    def pump(self, timeout: float = 0.1) -> None:
        """Đọc và in mọi bản tin đang chờ; đây là chỗ duy nhất in chiều server -> client."""
        alive = {name: bot for name, bot in self.bots.items() if bot is not None}
        if not alive:
            return
        ready, _, _ = select.select([bot.sock for bot in alive.values()], [], [], timeout)
        for name, bot in alive.items():
            if bot.sock not in ready:
                continue
            try:
                bot._receive_once(0)
            except DemoError as exc:
                print(f"  [!] {exc}")
                continue
            for message in bot._messages:
                self._absorb(name, message)
            bot._messages.clear()

    def _absorb(self, name: str, message: dict[str, Any]) -> None:
        kind = message.get("type")
        print(f"  {name.upper()} <- {kind}{_message_details(message)}")
        if kind == "error":
            print(f"      {message.get('code')}: {message.get('message')}")
        if kind in ("login", "create_user") and message.get("playerId"):
            self.ids[name] = str(message["playerId"])
        if kind == "invite":
            self.invite_id = message.get("inviteId")
        if kind == "game_state":
            if str(message.get("room_id")) != self.room_id:
                self.finished = False
            self.room_id = str(message.get("room_id"))
            self.board = message.get("board")
            print(f"      (bàn cờ đang có {_state_move_count(message)} nước)")
        if kind == "online_players":
            for row in message.get("players", []):
                print(f"      online: playerId={row['playerId']} | {row['username']} | {row['status']}")
        if kind == "player_disconnected":
            print(f"      >>> {message.get('playerId')} rớt mạng, còn {message.get('reconnectTimeLeft')}s để vào lại")
        if kind == "player_reconnected":
            print(f"      >>> {message.get('playerId')} đã vào lại phòng")
        if kind == "game_result":
            self.finished = True
            print(f"      >>> KẾT QUẢ: {message.get('result')} (lý do: {message.get('reason') or 'thắng trên bàn cờ'})")

    def wait_until(self, dieu_kien, seconds: float) -> bool:
        """Cho toi khi dieu_kien dung, hoac het gio; van in bao tin nhu thuong."""
        import time

        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if dieu_kien():
                return True
            self.pump(0.1)
        return dieu_kien()

    def wait(self, seconds: float) -> None:
        import time

        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.pump(0.2)

    # --- các lệnh -----------------------------------------------------
    def cmd_login(self) -> None:
        suffix = uuid4().hex[:8]
        for name in ("x", "o"):
            if self.bots[name] is not None:
                self.bots[name].close()
            username = f"manual_{name}_{suffix}"
            bot = TcpDemoClient(f"Bot {name.upper()}", HOST, PORT)
            bot.send({"type": "create_user", "username": username, "password": DEMO_PASSWORD})
            bot.send({"type": "login", "username": username, "password": DEMO_PASSWORD})
            bot.username = username
            self.bots[name] = bot
            self.usernames[name] = username
        self.wait_until(lambda: len(self.ids) == 2, 3.0)
        print(f"  [OK] x={self.usernames['x']} (id={self.ids.get('x')}), "
              f"o={self.usernames['o']} (id={self.ids.get('o')})")

    def cmd_invite(self) -> None:
        self.invite_id = f"manual_{uuid4().hex[:8]}"
        self._bot("x").send(
            {"type": "invite", "toPlayerId": self.ids["o"], "inviteId": self.invite_id}
        )

    def cmd_answer(self, accept: bool) -> None:
        if not self.invite_id:
            print("  [!] chưa có lời mời nào.")
            return
        kind = "accept_invite" if accept else "reject_invite"
        self._bot("o").send({"type": kind, "inviteId": self.invite_id})

    def cmd_disconnect(self, name: str) -> None:
        bot = self._bot(name)
        print(f"  [Sự cố] đóng socket của bot {name.upper()} ({bot.socket_label})")
        bot.close()
        self.bots[name] = None

    def cmd_reconnect(self, name: str) -> None:
        if self.bots[name] is not None:
            print(f"  [!] bot {name.upper()} đang kết nối rồi.")
            return
        bot = TcpDemoClient(f"Bot {name.upper()}", HOST, PORT)
        bot.send({"type": "login", "username": self.usernames[name], "password": DEMO_PASSWORD})
        bot.username = self.usernames[name]
        self.bots[name] = bot

    def cmd_move(self, name: str, row: int, col: int) -> None:
        self._bot(name).send(
            {
                "type": "make_move",
                "room_id": self.room_id,
                "playerId": self.ids[name],
                "row": row,
                "col": col,
            }
        )

    def _so_nuoc(self) -> int:
        return _state_move_count({"board": self.board or []})

    def cmd_auto(self, count: int | None) -> None:
        # Vua `accept` xong thi game_state con dang tren duong ve: cho no mot nhip.
        if not self.wait_until(lambda: self.room_id and self.board is not None, 2.0):
            print("  [!] chưa vào phòng nào; chạy `invite` rồi `accept` trước.")
            return
        da_danh = 0
        while count is None or da_danh < count:
            if self.finished:
                print("  [i] ván đã kết thúc, dừng auto.")
                return
            played = self._so_nuoc()
            if played >= len(SCRIPT):
                print("  [!] ván mẫu đã đánh hết; dùng `move` để đi nước tự chọn.")
                return
            name, row, col = SCRIPT[played]
            if self.bots[name] is None:
                print(f"  [!] bot {name.upper()} đang mất kết nối, dừng auto.")
                return
            self.cmd_move(name, row, col)
            # Doi server xac nhan roi moi di tiep: ban cham mot nhip thi nuoc
            # sau se bi tu choi NOT_YOUR_TURN va ca chuoi lech theo.
            moi = self.wait_until(
                lambda cu=played: self._so_nuoc() > cu or self.finished, 3.0
            )
            if not moi:
                print("  [!] server chưa xác nhận nước vừa gửi, dừng auto.")
                return
            da_danh += 1

    def cmd_board(self) -> None:
        if not self.board:
            print("  [!] chưa có bàn cờ nào.")
            return
        ky_hieu = {0: ".", 1: "X", 2: "O"}
        for row in self.board[:10]:
            print("    " + " ".join(ky_hieu.get(cell, "?") for cell in row[:10]))

    def cmd_players(self) -> None:
        bot = next((b for b in self.bots.values() if b is not None), None)
        if bot is None:
            print("  [!] không còn bot nào đang kết nối.")
            return
        bot.send({"type": "online_players"})
        self.wait(0.5)

    def _bot(self, name: str) -> TcpDemoClient:
        bot = self.bots.get(name)
        if bot is None:
            raise DemoError(f"bot {name.upper()} đang mất kết nối, dùng `reconnect {name}` trước.")
        return bot

    def close(self) -> None:
        for bot in self.bots.values():
            if bot is not None:
                bot.close()


def _handle(console: Console, line: str) -> bool:
    parts = line.split()
    if not parts:
        return True
    cmd, args = parts[0].lower(), parts[1:]

    if cmd in ("quit", "exit"):
        return False
    if cmd == "help":
        print(HELP)
    elif cmd == "login":
        console.cmd_login()
    elif cmd == "invite":
        console.cmd_invite()
    elif cmd == "accept":
        console.cmd_answer(True)
    elif cmd == "reject":
        console.cmd_answer(False)
    elif cmd == "disconnect":
        console.cmd_disconnect(args[0])
    elif cmd == "reconnect":
        console.cmd_reconnect(args[0])
    elif cmd == "move":
        console.cmd_move(args[0], int(args[1]), int(args[2]))
    elif cmd == "auto":
        console.cmd_auto(int(args[0]) if args else None)
    elif cmd == "board":
        console.cmd_board()
    elif cmd == "players":
        console.cmd_players()
    elif cmd == "wait":
        console.wait(float(args[0]) if args else 5.0)
    else:
        print(f"  [!] không hiểu lệnh {cmd!r}; gõ `help`.")
    return True


def main() -> int:
    console = Console()
    try:
        while True:
            # Vừa nghe socket vừa chờ bàn phím: bản tin server gửi trong lúc
            # bạn chưa gõ gì vẫn hiện ra ngay.
            sys.stdout.write("\n> ")
            sys.stdout.flush()
            while True:
                ready, _, _ = select.select([sys.stdin], [], [], 0.2)
                if ready:
                    break
                console.pump(0.0)
            line = sys.stdin.readline()
            if not line:
                break
            try:
                if not _handle(console, line.strip()):
                    break
            except (DemoError, IndexError, ValueError) as exc:
                print(f"  [!] {exc}")
            console.pump(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        console.close()
    print("\nĐã đóng cả hai bot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
