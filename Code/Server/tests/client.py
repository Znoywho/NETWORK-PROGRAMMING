
from __future__ import annotations

import json
import socket
import struct

HOST = "127.0.0.1"
PORT = 8765
HEADER_SIZE = 4  # unsigned 32-bit big-endian


class Client:
    def __init__(self, name: str):
        self.name = name
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        self._buf = bytearray()

    def send(self, msg: dict) -> None:
        body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        frame = struct.pack(">I", len(body)) + body
        print(f"[{self.name}] -> {msg}")
        self.sock.sendall(frame)

    def _read_exact(self, n: int, timeout: float) -> bytes:
        self.sock.settimeout(timeout)
        while len(self._buf) < n:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError(f"[{self.name}] Server đóng kết nối.")
            self._buf.extend(chunk)
        data = bytes(self._buf[:n])
        del self._buf[:n]
        return data

    def recv_one(self, timeout: float = 3.0) -> dict:
        """Nhận đúng 1 frame, trả về JSON đã parse."""
        header = self._read_exact(HEADER_SIZE, timeout)
        (body_len,) = struct.unpack(">I", header)
        body = self._read_exact(body_len, timeout)
        msg = json.loads(body.decode("utf-8"))
        print(f"[{self.name}] <- {msg}")
        return msg

    def request(self, msg: dict) -> dict:
        """Gửi 1 message, nhận về reply đầu tiên (dành cho request-reply đơn giản)."""
        self.send(msg)
        return self.recv_one()

    def close(self) -> None:
        self.sock.close()


def find_room_id(*payloads: dict) -> str:
    for p in payloads:
        if "room_id" in p:
            return p["room_id"]
    raise RuntimeError("Không tìm thấy room_id trong các payload đã nhận.")


def main() -> None:
    a = Client("A")
    b = Client("B")

    # 1) Tạo user (nếu đã tồn tại sẽ nhận USER_ALREADY_EXIST, bỏ qua được)
    a.request({"type": "create_user", "username": "playerA", "password": "pass123"})
    b.request({"type": "create_user", "username": "playerB", "password": "pass123"})

    # 2) Login -> mỗi client nhận 2 message: reply login + broadcast online_players
    login_a = a.recv_one() if False else a.request({"type": "login", "username": "playerA", "password": "pass123"})
    a.recv_one()  # broadcast online_players
    login_b = b.request({"type": "login", "username": "playerB", "password": "pass123"})
    b.recv_one()  # broadcast online_players
    a.recv_one()  # A cũng nhận broadcast online_players khi B login

    a_id = login_a["playerId"]
    b_id = login_b["playerId"]
    print(f"playerA id={a_id}  playerB id={b_id}")

    # 3) Xem danh sách online (không bắt buộc, chỉ để demo)
    a.request({"type": "online_players"})

    # 4) A mời B
    invite_id = "invite-1"
    a.request({"type": "invite", "toPlayerId": b_id, "inviteId": invite_id})
    invite_push = b.recv_one()  # B nhận push "invite"

    # 5) B chấp nhận -> cả 2 nhận game_state (chứa room_id)
    accept_reply = b.request({"type": "accept_invite", "inviteId": invite_id})
    state_a = a.recv_one()  # A cũng nhận game_state
    room_id = find_room_id(accept_reply, state_a)
    print(f"Room bắt đầu: {room_id}")

    # 6) Chơi: giả định A đi trước là X, B là O.
    #    A thắng bằng 5 quân liên tiếp trên hàng 0.
    moves = [
        (a_id, 0, 0), (b_id, 1, 0),
        (a_id, 0, 1), (b_id, 1, 1),
        (a_id, 0, 2), (b_id, 1, 2),
        (a_id, 0, 3), (b_id, 1, 3),
        (a_id, 0, 4),  # 5 liên tiếp -> A thắng
    ]

    for player_id, row, col in moves:
        mover, watcher = (a, b) if player_id == a_id else (b, a)
        mover.send({"type": "make_move", "playerId": player_id, "room_id": room_id, "row": row, "col": col})
        mover.recv_one()   # game_state (hoặc error nếu sai lượt)
        watcher.recv_one()  # đối thủ cũng nhận game_state

    for _ in range(2):
        a.recv_one()
    for _ in range(2):
        b.recv_one()

    a.close()
    b.close()
    print("Xong ván test!")


if __name__ == "__main__":
    main()
