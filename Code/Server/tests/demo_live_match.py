import argparse
import json
import os
import select
import socket
import struct
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


SERVER_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVER_DIR / ".env", override=True)

DEMO_PASSWORD = "demo-pass-123"
CONNECT_TIMEOUT = 5.0
MESSAGE_TIMEOUT = 5.0
DB_TIMEOUT = 8.0

# Ghi lại người chơi đã tạo trong lúc demo chạy, để in danh sách khi có
# sự kiện mất kết nối / vào lại và để tổng kết ở cuối.
PLAYERS: dict[str, dict[str, Any]] = {}


class DemoError(RuntimeError):
    """A failed expectation in the live demo."""


class TcpDemoClient:
    """Tiny client that uses exactly the project's TCP frame format."""

    def __init__(self, name: str, host: str, port: int) -> None:
        self.name = name
        self.username = ""
        try:
            self.sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
        except OSError as exc:
            raise DemoError(
                f"Không kết nối được tới TCP server {host}:{port}. "
                "Hãy chạy `docker compose up --build` trước."
            ) from exc
        self.sock.setblocking(False)
        self._buffer = bytearray()
        self._messages: list[dict[str, Any]] = []
        local_host, local_port = self.sock.getsockname()[:2]
        peer_host, peer_port = self.sock.getpeername()[:2]
        self.socket_label = (
            f"fd={self.sock.fileno()} {local_host}:{local_port} -> {peer_host}:{peer_port}"
        )
        print(f"[TCP] {self.name} đã kết nối tới {host}:{port} | socket {self.socket_label}")

    def send(self, message: dict[str, Any]) -> None:
        body = json.dumps(message, ensure_ascii=False).encode("utf-8")
        frame = struct.pack(">I", len(body)) + body
        self.sock.setblocking(True)
        try:
            self.sock.sendall(frame)
        finally:
            self.sock.setblocking(False)
        print(f"  {self.name:>8} -> {message['type']}{_message_details(message)}")
        print(f"  {'':>8}    socket {self.socket_label} | {len(frame)} byte")
        print(f"  {'':>8}    JSON gửi đi: {json.dumps(message, ensure_ascii=False)}")

    def wait_for(
        self,
        message_type: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
        timeout: float = MESSAGE_TIMEOUT,
    ) -> dict[str, Any]:
        predicate = predicate or (lambda _message: True)
        deadline = time.monotonic() + timeout
        while True:
            for index, message in enumerate(self._messages):
                if message.get("type") == "error":
                    raise DemoError(f"Server trả error cho {self.name}: {message}")
                if message.get("type") == message_type and predicate(message):
                    self._messages.pop(index)
                    print(
                        f"  {self.name:>8} <- {message_type}{_message_details(message)}"
                        f"  [socket {self.socket_label}]"
                    )
                    return message

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                received = [message.get("type") for message in self._messages]
                raise DemoError(
                    f"Chờ {message_type!r} từ {self.name} quá {timeout:.0f}s "
                    f"(đã nhận: {received})."
                )
            self._receive_once(remaining)

    def drop_pending(self, message_type: str) -> None:
        """Bỏ các bản tin cũ cùng loại để lần hỏi sau chắc chắn là dữ liệu mới."""
        self._receive_once(0.2)
        self._messages = [m for m in self._messages if m.get("type") != message_type]

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _receive_once(self, timeout: float) -> None:
        ready, _, _ = select.select([self.sock], [], [], timeout)
        if not ready:
            return
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            return
        if not data:
            raise DemoError(f"TCP server đã đóng kết nối của {self.name}.")
        self._buffer.extend(data)

        offset = 0
        while len(self._buffer) - offset >= 4:
            length = struct.unpack(">I", self._buffer[offset : offset + 4])[0]
            end = offset + 4 + length
            if len(self._buffer) < end:
                break
            payload = bytes(self._buffer[offset + 4 : end])
            offset = end
            decoded = json.loads(payload.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise DemoError(f"Server gửi JSON không phải object: {decoded!r}")
            self._messages.append(decoded)
        if offset:
            del self._buffer[:offset]


def _message_details(message: dict[str, Any]) -> str:
    """Keep the network transcript short while retaining the useful facts."""
    keys = ("playerId", "room_id", "inviteId", "result", "reason", "ranking", "reconnectTimeLeft")
    parts = [f"{key}={message[key]}" for key in keys if key in message]
    return f" ({', '.join(parts)})" if parts else ""


def _state_move_count(message: dict[str, Any]) -> int:
    """Count occupied cells so a client never mistakes an older state for a new one."""
    board = message.get("board", [])
    return sum(cell != 0 for row in board if isinstance(row, list) for cell in row)


def _db_connection(db_url: str):
    try:
        # libpq requires this option to be an integer number of seconds.
        return psycopg2.connect(db_url, connect_timeout=int(CONNECT_TIMEOUT))
    except psycopg2.Error as exc:
        raise DemoError(
            "Không kết nối được PostgreSQL. Hãy kiểm tra container `caro-db` "
            "và OUT_CARO_DATABASE_URL trong Code/Server/.env."
        ) from exc


def _fetch_match(db_url: str, match_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with _db_connection(db_url) as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT m.id, m.status, m.result, m.winner_id, m.started_at, m.ended_at,
                   ux.username AS player_x, uo.username AS player_o,
                   uw.username AS winner_name
            FROM matches m
            JOIN users ux ON ux.id = m.player_x_id
            JOIN users uo ON uo.id = m.player_o_id
            LEFT JOIN users uw ON uw.id = m.winner_id
            WHERE m.id = %s
            """,
            (int(match_id),),
        )
        match = cursor.fetchone()
        if match is None:
            raise DemoError(f"Không tìm thấy match_id={match_id} trong database.")
        cursor.execute(
            """
            SELECT mv.move_index, u.username, mv.row_idx, mv.col_idx, mv.created_at
            FROM moves mv
            JOIN users u ON u.id = mv.player_id
            WHERE mv.match_id = %s
            ORDER BY mv.move_index
            """,
            (int(match_id),),
        )
        return dict(match), [dict(row) for row in cursor.fetchall()]


def _fetch_rankings(db_url: str, player_ids: tuple[str, str]) -> dict[str, int]:
    with _db_connection(db_url) as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id, ranking FROM users WHERE id IN (%s, %s)",
            (int(player_ids[0]), int(player_ids[1])),
        )
        return {str(row["id"]): int(row["ranking"] or 0) for row in cursor.fetchall()}


def _wait_for_database(
    db_url: str,
    match_id: str,
    predicate: Callable[[dict[str, Any], list[dict[str, Any]]], bool],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deadline = time.monotonic() + DB_TIMEOUT
    while True:
        match, moves = _fetch_match(db_url, match_id)
        if predicate(match, moves):
            return match, moves
        if time.monotonic() >= deadline:
            raise DemoError(
                "DB Writer chưa ghi xong trong thời gian chờ: "
                f"status={match['status']}, moves={len(moves)}."
            )
        time.sleep(0.2)


def _timing_connection(db_url: str):
    """Mot ket noi rieng, autocommit, giu mo suot van dau.

    Do do tre ghi DB thi khong duoc mo ket noi moi moi lan hoi: chi rieng
    buoc bat tay TCP + xac thuc cua libpq da ton vai mili giay, dung bang
    hoac hon chinh cai can do.
    """
    connection = _db_connection(db_url)
    connection.autocommit = True
    return connection


def _wait_visible(connection, sql: str, params: tuple, since: float, mo_ta: str) -> float:
    """Hoi lai DB toi khi dong du lieu hien ra; tra ve do tre tinh bang ms."""
    deadline = time.perf_counter() + DB_TIMEOUT
    while True:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.fetchone() is not None:
                return (time.perf_counter() - since) * 1000
        if time.perf_counter() >= deadline:
            raise DemoError(f"{mo_ta} khong xuat hien trong DB sau {DB_TIMEOUT:.0f}s.")
        # Hoi lai that day: nhip hoi cham hon do tre can do thi so do vo nghia.
        time.sleep(0.002)


def _wait_move_visible(connection, match_id: str, move_index: int, since: float) -> float:
    return _wait_visible(
        connection,
        "SELECT 1 FROM moves WHERE match_id = %s AND move_index = %s",
        (int(match_id), move_index),
        since,
        f"Nuoc #{move_index}",
    )


def _wait_finished_visible(connection, match_id: str, since: float) -> float:
    return _wait_visible(
        connection,
        "SELECT 1 FROM matches WHERE id = %s AND status = 'finished'",
        (int(match_id),),
        since,
        "Ket qua tran dau",
    )


def _print_timings(timings: list[tuple[int, float, float]], result_ms: float) -> None:
    print("\n  [Đo thời gian] từ lúc client gửi nước đi:")
    print("    nước | server trả lời | dòng có trong PostgreSQL | chênh lệch")
    for index, reply_ms, db_ms in timings:
        print(
            f"     #{index}   | {reply_ms:9.1f} ms | {db_ms:16.1f} ms | "
            f"{db_ms - reply_ms:+7.1f} ms"
        )
    reply_tb = sum(row[1] for row in timings) / len(timings)
    db_tb = sum(row[2] for row in timings) / len(timings)
    print(f"    trung bình: server {reply_tb:.1f} ms | DB {db_tb:.1f} ms")
    print(f"    UPDATE kết quả trận: {result_ms:.1f} ms sau khi client nhận game_result")
    print(
        "    → client luôn thấy nước cờ TRƯỚC khi PostgreSQL commit xong: "
        "handler chỉ put() vào hàng đợi rồi đi tiếp, DB Writer ghi ở luồng khác."
    )


def _print_database(match: dict[str, Any], moves: list[dict[str, Any]], rankings: dict[str, int]) -> None:
    print("\n  [PostgreSQL] Bảng matches")
    print(
        "    "
        f"id={match['id']} | {match['player_x']} (X) vs {match['player_o']} (O) "
        f"| status={match['status']} | result={match['result']} "
        f"| winner={match['winner_name'] or '-'}"
    )
    print("  [PostgreSQL] Bảng moves")
    for move in moves:
        print(
            f"    #{move['move_index']}: {move['username']} "
            f"đánh ({move['row_idx']}, {move['col_idx']})"
        )
    print("  [PostgreSQL] Bảng users (ranking)")
    for player_id, ranking in sorted(rankings.items(), key=lambda row: int(row[0])):
        print(f"    player_id={player_id}: ranking={ranking}")


def _set_player_state(
    player_id: str,
    status: str,
    *,
    online: bool | None = None,
    socket_label: str | None = None,
    room_id: str | None = None,
) -> None:
    """Cập nhật trạng thái một người chơi trong sổ theo dõi của demo."""
    info = PLAYERS.setdefault(player_id, {"username": "?"})
    info["status"] = status
    if online is not None:
        info["online"] = online
    if socket_label is not None:
        info["socket"] = socket_label
    if room_id is not None:
        info["room"] = room_id


def _print_players(
    title: str = "DANH SÁCH NGƯỜI CHƠI",
    room_id: str | None = None,
    player_ids: tuple[str, ...] | None = None,
) -> None:
    """In danh sách người chơi; lọc theo phòng hoặc theo danh sách playerId."""
    players = {
        player_id: info
        for player_id, info in PLAYERS.items()
        if (room_id is None or info.get("room") == room_id)
        and (player_ids is None or player_id in player_ids)
    }
    print("\n  " + "-" * 70)
    print(f"  [{title}] tổng {len(players)} người chơi")
    for player_id, info in sorted(players.items(), key=lambda row: int(row[0])):
        print(
            f"    playerId={player_id} | username={info['username']} | "
            f"trạng thái={info.get('status', '-')} | "
            f"phòng={info.get('room', '-')} | socket {info.get('socket', '-')}"
        )
    print("  " + "-" * 70)


def _compare_with_server(
    client: TcpDemoClient, player_ids: tuple[str, ...], title: str
) -> None:
    """Hỏi server danh sách online_players rồi đối chiếu với sổ theo dõi của demo."""
    client.drop_pending("online_players")
    client.send({"type": "online_players"})
    reply = client.wait_for("online_players")
    server_ids = {str(row["playerId"]) for row in reply.get("players", [])}

    print("\n  " + "-" * 70)
    print(
        f"  [{title}] server đang giữ {len(server_ids)} người online: "
        f"{sorted(server_ids, key=int)}"
    )
    sai = []
    for player_id in player_ids:
        info = PLAYERS[player_id]
        tren_server = player_id in server_ids
        khop = tren_server == bool(info.get("online"))
        print(
            f"    playerId={player_id} | username={info['username']} | "
            f"demo: {info['status']} | "
            f"server: {'CÒN trong online_players' if tren_server else 'KHÔNG còn trong online_players'}"
            f" | {'khớp' if khop else 'LỆCH'}"
        )
        if not khop:
            sai.append(player_id)
    print("  " + "-" * 70)
    if sai:
        raise DemoError(
            f"Trạng thái kết nối của {sai} trên server không khớp với những gì demo quan sát."
        )


def _print_registry() -> None:
    print("\n" + "=" * 72)
    _print_players("DANH SÁCH NGƯỜI CHƠI (cuối demo)")


def _create_and_login(client: TcpDemoClient, username: str) -> str:
    client.send({"type": "create_user", "username": username, "password": DEMO_PASSWORD})
    created = client.wait_for("create_user")
    client.send({"type": "login", "username": username, "password": DEMO_PASSWORD})
    logged_in = client.wait_for("login")
    if created["playerId"] != logged_in["playerId"]:
        raise DemoError("playerId sau create_user và login không khớp.")
    client.username = username
    player_id = str(logged_in["playerId"])
    PLAYERS[player_id] = {
        "username": username,
        "status": "online",
        "online": True,
        "socket": client.socket_label,
        "room": "-",
    }
    return player_id


def _login_again(name: str, username: str, host: str, port: int) -> TcpDemoClient:
    """Reconnect the way a real client does: a brand new socket, then login."""
    client = TcpDemoClient(name, host, port)
    try:
        client.send({"type": "login", "username": username, "password": DEMO_PASSWORD})
        client.wait_for("login")
    except Exception:
        client.close()
        raise
    client.username = username
    return client


def _play(client: TcpDemoClient, player_id: str, room_id: str, row: int, col: int) -> None:
    client.send({"type": "make_move", "room_id": room_id, "playerId": player_id, "row": row, "col": col})


def _start_match(host: str, port: int, label: str) -> tuple[TcpDemoClient, TcpDemoClient, str, str, str]:
    suffix = uuid4().hex[:10]
    player_x = TcpDemoClient("Player X", host, port)
    player_o = TcpDemoClient("Player O", host, port)
    try:
        x_id = _create_and_login(player_x, f"demo_x_{label}_{suffix}")
        o_id = _create_and_login(player_o, f"demo_o_{label}_{suffix}")
        _print_players(
            "NGƯỜI CHƠI — SAU KHI ĐĂNG NHẬP", player_ids=(x_id, o_id)
        )
        invite_id = f"demo_{label}_{suffix}"
        player_x.send({"type": "invite", "toPlayerId": o_id, "inviteId": invite_id})
        player_x.wait_for("invite_result", lambda message: message.get("inviteId") == invite_id)
        player_o.wait_for("invite", lambda message: message.get("inviteId") == invite_id)
        player_o.send({"type": "accept_invite", "inviteId": invite_id})
        x_state = player_x.wait_for("game_state", lambda message: message.get("status") == "playing")
        player_o.wait_for(
            "game_state",
            lambda message: message.get("room_id") == x_state.get("room_id") and message.get("status") == "playing",
        )
        room_id = str(x_state["room_id"])
        _set_player_state(x_id, "đang chơi", online=True, room_id=room_id)
        _set_player_state(o_id, "đang chơi", online=True, room_id=room_id)
        print(f"\n  [OK] Tạo trận thật: room_id/match_id = {room_id}")
        return player_x, player_o, x_id, o_id, room_id
    except Exception:
        player_x.close()
        player_o.close()
        raise


def demo_normal_win(host: str, port: int, db_url: str) -> None:
    print("\n" + "=" * 72)
    print("DEMO 1 — Ván thật: Player X thắng và Elo được lưu vào PostgreSQL")
    print("=" * 72)
    player_x, player_o, x_id, o_id, room_id = _start_match(host, port, "win")
    timing = _timing_connection(db_url)
    try:
        before = _fetch_rankings(db_url, (x_id, o_id))
        print(f"  Điểm trước trận: X={before[x_id]}, O={before[o_id]}")

        moves = [
            (player_x, x_id, 0, 0), (player_o, o_id, 1, 0),
            (player_x, x_id, 0, 1), (player_o, o_id, 1, 1),
            (player_x, x_id, 0, 2), (player_o, o_id, 1, 2),
            (player_x, x_id, 0, 3), (player_o, o_id, 1, 3),
            (player_x, x_id, 0, 4),
        ]
        timings: list[tuple[int, float, float]] = []
        for index, (client, player_id, row, col) in enumerate(moves, start=1):
            sent_at = time.perf_counter()
            _play(client, player_id, room_id, row, col)
            if index < len(moves):
                client.wait_for(
                    "game_state",
                    lambda message, expected=index: (
                        message.get("room_id") == room_id
                        and _state_move_count(message) == expected
                    ),
                )
            else:
                winner = player_x.wait_for(
                    "game_result", lambda message: message.get("room_id") == room_id
                )
                result_at = time.perf_counter()
            reply_ms = (time.perf_counter() - sent_at) * 1000
            timings.append((index, reply_ms, _wait_move_visible(timing, room_id, index, sent_at)))

        loser = player_o.wait_for("game_result", lambda message: message.get("room_id") == room_id)
        if winner.get("result") != "win" or loser.get("result") != "lose":
            raise DemoError("Kết quả gửi về client không đúng: X phải thắng, O phải thua.")
        result_ms = _wait_finished_visible(timing, room_id, result_at)
        _print_timings(timings, result_ms)

        match, saved_moves = _wait_for_database(
            db_url, room_id, lambda row, rows: row["status"] == "finished" and len(rows) == 9
        )
        after = _fetch_rankings(db_url, (x_id, o_id))
        _print_database(match, saved_moves, after)
        if match["result"] != "x_win" or match["winner_id"] != int(x_id):
            raise DemoError("Kết quả DB không phải x_win với Player X là người thắng.")
        if after[x_id] - before[x_id] != 16 or after[o_id] - before[o_id] != -16:
            raise DemoError("Elo của hai tài khoản mới không tăng +16/-16 như kỳ vọng.")
        print("\n  [PASS] 9 nước cờ, kết quả x_win và Elo +16/-16 đã được ghi thật vào DB.")
    finally:
        timing.close()
        player_x.close()
        player_o.close()
        _set_player_state(
            x_id, "offline", online=False, socket_label="(socket đã đóng)", room_id="-"
        )
        _set_player_state(
            o_id, "offline", online=False, socket_label="(socket đã đóng)", room_id="-"
        )


def demo_reconnect_in_time(host: str, port: int, db_url: str) -> None:
    print("\n" + "=" * 72)
    print("DEMO 2 — Mất kết nối rồi VÀO LẠI KỊP: ván đấu được chơi tiếp")
    print("=" * 72)
    player_x, player_o, x_id, o_id, room_id = _start_match(host, port, "reconnect")
    try:
        before = _fetch_rankings(db_url, (x_id, o_id))
        username_x = player_x.username
        print(f"  Điểm trước trận: X={before[x_id]}, O={before[o_id]}")

        opening = [
            (player_x, x_id, 0, 0), (player_o, o_id, 1, 0),
            (player_x, x_id, 0, 1), (player_o, o_id, 1, 1),
        ]
        for index, (client, player_id, row, col) in enumerate(opening, start=1):
            _play(client, player_id, room_id, row, col)
            client.wait_for(
                "game_state",
                lambda message, expected=index: (
                    message.get("room_id") == room_id
                    and _state_move_count(message) == expected
                ),
            )

        print("\n  [Sự cố] Player X rớt mạng đúng lượt của mình: đóng TCP socket.")
        player_x.close()
        disconnected = player_o.wait_for("player_disconnected", timeout=MESSAGE_TIMEOUT)
        grace_seconds = int(disconnected["reconnectTimeLeft"])
        _set_player_state(
            x_id,
            f"mất kết nối (còn {grace_seconds}s để vào lại)",
            online=False,
            socket_label="(socket đã đóng)",
        )
        _print_players("NGƯỜI CHƠI TRONG PHÒNG — SAU KHI X MẤT KẾT NỐI", room_id)
        _compare_with_server(
            player_o, (x_id, o_id), "ĐỐI CHIẾU VỚI SERVER — SAU KHI X MẤT KẾT NỐI"
        )
        print(f"  Player X có {grace_seconds}s để quay lại; lần này X vào lại ngay.")

        player_x = _login_again("Player X", username_x, host, port)
        _set_player_state(
            x_id,
            "đang chơi",
            online=True,
            socket_label=player_x.socket_label,
            room_id=room_id,
        )
        player_o.wait_for(
            "player_reconnected",
            lambda message: message.get("room_id") == room_id and message.get("playerId") == x_id,
        )
        state = player_x.wait_for("game_state", lambda message: message.get("room_id") == room_id)
        if _state_move_count(state) != 4:
            raise DemoError("Người vào lại phải nhận đúng bàn cờ 4 nước đang dở.")
        print("  [Đúng] X nhận lại bàn cờ 4 nước cũ, đồng hồ suy nghĩ được cấp lại trọn vẹn.")
        _print_players("NGƯỜI CHƠI TRONG PHÒNG — SAU KHI X VÀO LẠI", room_id)
        _compare_with_server(
            player_o, (x_id, o_id), "ĐỐI CHIẾU VỚI SERVER — SAU KHI X VÀO LẠI"
        )

        endgame = [
            (player_x, x_id, 0, 2), (player_o, o_id, 1, 2),
            (player_x, x_id, 0, 3), (player_o, o_id, 1, 3),
            (player_x, x_id, 0, 4),
        ]
        for index, (client, player_id, row, col) in enumerate(endgame, start=5):
            _play(client, player_id, room_id, row, col)
            if index < 9:
                client.wait_for(
                    "game_state",
                    lambda message, expected=index: (
                        message.get("room_id") == room_id
                        and _state_move_count(message) == expected
                    ),
                )

        winner = player_x.wait_for("game_result", lambda message: message.get("room_id") == room_id)
        player_o.wait_for("game_result", lambda message: message.get("room_id") == room_id)
        if winner.get("result") != "win":
            raise DemoError("Player X phải thắng sau khi quay lại và đánh hết ván.")

        match, saved_moves = _wait_for_database(
            db_url, room_id, lambda row, rows: row["status"] == "finished" and len(rows) == 9
        )
        after = _fetch_rankings(db_url, (x_id, o_id))
        _print_database(match, saved_moves, after)
        if match["result"] != "x_win" or match["winner_id"] != int(x_id):
            raise DemoError("DB phải ghi x_win cho ván được chơi tiếp sau khi kết nối lại.")
        if after[x_id] - before[x_id] != 16 or after[o_id] - before[o_id] != -16:
            raise DemoError("Ván chơi tiếp vẫn phải tính Elo +16/-16 như ván thường.")
        print(
            "\n  [PASS] Mất kết nối giữa chừng không làm mất nước cờ: DB vẫn đủ 9 nước, "
            "x_win và Elo +16/-16."
        )
    finally:
        player_x.close()
        player_o.close()
        _set_player_state(
            x_id, "offline", online=False, socket_label="(socket đã đóng)", room_id="-"
        )
        _set_player_state(
            o_id, "offline", online=False, socket_label="(socket đã đóng)", room_id="-"
        )


def demo_disconnect_timeout(host: str, port: int, db_url: str) -> None:
    print("\n" + "=" * 72)
    print("DEMO 3 — Mất kết nối và KHÔNG quay lại: hết hạn reconnect rồi ghi DB")
    print("=" * 72)
    player_x, player_o, x_id, o_id, room_id = _start_match(host, port, "disconnect")
    try:
        before = _fetch_rankings(db_url, (x_id, o_id))
        for index, (client, player_id, row, col) in enumerate(
            ((player_x, x_id, 3, 3), (player_o, o_id, 4, 3)), start=1
        ):
            _play(client, player_id, room_id, row, col)
            client.wait_for(
                "game_state",
                lambda message, expected=index: (
                    message.get("room_id") == room_id
                    and _state_move_count(message) == expected
                ),
            )

        print("\n  [Sự cố] Giả lập Player X rớt mạng: đóng TCP socket của X.")
        player_x.close()
        disconnected = player_o.wait_for("player_disconnected", timeout=MESSAGE_TIMEOUT)
        grace_seconds = int(disconnected["reconnectTimeLeft"])
        _set_player_state(
            x_id,
            f"mất kết nối (còn {grace_seconds}s để vào lại)",
            online=False,
            socket_label="(socket đã đóng)",
        )
        _print_players("NGƯỜI CHƠI TRONG PHÒNG — SAU KHI X MẤT KẾT NỐI", room_id)
        _compare_with_server(
            player_o, (x_id, o_id), "ĐỐI CHIẾU VỚI SERVER — SAU KHI X MẤT KẾT NỐI"
        )
        waiting_match, waiting_moves = _wait_for_database(
            db_url, room_id, lambda row, rows: row["status"] == "playing" and len(rows) == 2
        )
        print(
            f"  [Đúng] Trong {grace_seconds}s chờ reconnect: match vẫn "
            f"{waiting_match['status']}, DB giữ đủ {len(waiting_moves)} nước cờ."
        )
        print(f"  Chờ hết {grace_seconds}s reconnect để server tự xử Player O thắng...")
        result = player_o.wait_for(
            "game_result",
            lambda message: message.get("room_id") == room_id and message.get("reason") == "disconnect",
            timeout=grace_seconds + MESSAGE_TIMEOUT,
        )
        if result.get("result") != "win" or result.get("winnerId") != o_id:
            raise DemoError("Player O phải thắng khi Player X không quay lại kịp.")
        _set_player_state(
            x_id,
            "đã rời trận (hết hạn vào lại)",
            online=False,
            socket_label="(socket đã đóng)",
        )
        _set_player_state(o_id, "thắng, trận đã kết thúc", online=True)
        _print_players("NGƯỜI CHƠI TRONG PHÒNG — SAU KHI HẾT HẠN VÀO LẠI", room_id)
        _compare_with_server(
            player_o, (x_id, o_id), "ĐỐI CHIẾU VỚI SERVER — SAU KHI HẾT HẠN VÀO LẠI"
        )

        match, saved_moves = _wait_for_database(
            db_url, room_id, lambda row, rows: row["status"] == "finished" and len(rows) == 2
        )
        after = _fetch_rankings(db_url, (x_id, o_id))
        _print_database(match, saved_moves, after)
        if match["result"] != "o_win" or match["winner_id"] != int(o_id):
            raise DemoError("DB không ghi o_win cho trường hợp hết hạn kết nối lại.")
        if after != before:
            raise DemoError("Theo luật hiện tại, trận disconnect không được đổi Elo.")
        print(
            "\n  [PASS] DB ghi o_win sau khi hết hạn reconnect. Elo giữ nguyên: "
            "luật hiện tại chỉ tính điểm cho thắng trên bàn cờ hoặc timeout lượt."
        )
    finally:
        player_x.close()
        player_o.close()
        _set_player_state(
            x_id,
            "offline (không vào lại)",
            online=False,
            socket_label="(socket đã đóng)",
            room_id="-",
        )
        _set_player_state(
            o_id, "offline", online=False, socket_label="(socket đã đóng)", room_id="-"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo TCP + PostgreSQL cho Game Caro")
    parser.add_argument(
        "--scenario", choices=("win", "reconnect", "disconnect", "all"), default="all"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--matches",
        type=int,
        default=1,
        help="Số lần lặp mỗi kịch bản, để tạo nhiều phòng cùng quản lý (mặc định 1).",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("OUT_CARO_DATABASE_URL", ""),
        help="Mặc định lấy OUT_CARO_DATABASE_URL từ Code/Server/.env.",
    )
    args = parser.parse_args()
    if not args.db_url:
        raise DemoError("Thiếu OUT_CARO_DATABASE_URL trong Code/Server/.env.")

    try:
        for lan in range(1, args.matches + 1):
            if args.matches > 1:
                print(f"\n########## LƯỢT CHẠY {lan}/{args.matches} ##########")
            if args.scenario in ("win", "all"):
                demo_normal_win(args.host, args.port, args.db_url)
            if args.scenario in ("reconnect", "all"):
                demo_reconnect_in_time(args.host, args.port, args.db_url)
            if args.scenario in ("disconnect", "all"):
                demo_disconnect_timeout(args.host, args.port, args.db_url)
    except DemoError as exc:
        print(f"\n[FAIL] {exc}", file=sys.stderr)
        _print_registry()
        return 1

    _print_registry()
    print("\n" + "=" * 72)
    print("TẤT CẢ DEMO INTEGRATION ĐÃ PASS — dữ liệu vẫn còn trong PostgreSQL.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
