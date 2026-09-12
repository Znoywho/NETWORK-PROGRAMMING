"""
Server Dashboard - Giao diện pygame để theo dõi client (Player) và bàn cờ (Room)
đang chạy trên server caro online.

CÁCH DÙNG THỰC TẾ:
    Dashboard này CHỈ ĐỌC dữ liệu từ PlayerManager / RoomManager của bạn
    (2 class bạn đã đưa). Nó không tự tạo player/room thật, chỉ hiển thị.

    Chạy nó trong 1 thread riêng song song với server (socket/websocket) chính:

        from server_dashboard import run_dashboard
        import threading

        threading.Thread(
            target=run_dashboard,
            args=(player_manager, room_manager),
            daemon=True,
        ).start()

    Vì PlayerManager/RoomManager đều dùng threading.Lock nên đọc dữ liệu
    từ thread khác (thread của pygame) là an toàn.

    Lưu ý: RoomManager bạn đưa chưa có method liệt kê toàn bộ room, nên
    dashboard tự truy cập room_manager._rooms bên trong lock của chính nó
    (xem hàm _snapshot_rooms). Nếu muốn sạch hơn, bạn có thể thêm method:

        def list_rooms(self) -> list[Room]:
            with self._lock:
                return list(self._rooms.values())

    và đổi _snapshot_rooms để gọi room_manager.list_rooms().

Khi chạy trực tiếp file này (python server_dashboard.py), nó sẽ tự tạo
dữ liệu giả (fake players + rooms + nước đi ngẫu nhiên) để bạn xem trước
giao diện mà không cần server thật.
"""

from __future__ import annotations

import random
import threading
import time
import uuid
from dataclasses import dataclass, field

import pygame

# ----------------------------------------------------------------------------
# Cấu hình giao diện
# ----------------------------------------------------------------------------
from app.ui.style import (
    COL_ACCENT,
    COL_BG,
    COL_BORDER,
    COL_GRID,
    COL_O,
    COL_PANEL,
    COL_PANEL_ALT,
    COL_SELECTED,
    COL_TEXT,
    COL_TEXT_DIM,
    COL_X,
    FPS,
    HEIGHT,
    SIDEBAR_W,
    STATUS_COLOR,
    WIDTH,
    Button,
    _enum_val,
    _snapshot_players,
    _snapshot_rooms,
    draw_text,
)


# ----------------------------------------------------------------------------
# Dashboard chính
# ----------------------------------------------------------------------------
class ServerDashboard:
    def __init__(self, player_manager, room_manager):
        self.player_manager = player_manager
        self.room_manager = room_manager

        pygame.init()
        pygame.display.set_caption("Caro Server Dashboard")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font("app/assests/font/MinecraftDefault-Regular.ttf", 16)
        self.font_bold = pygame.font.Font("app/assests/font/MinecraftDefault-Bold.ttf", 18)
        self.font_small = pygame.font.Font("app/assests/font/MinecraftDefault-Regular.ttf", 13)
        self.font_title = pygame.font.Font("app/assests/font/MinecraftDefault-Regular.ttf", 24)

        self.tab = "rooms"  # "rooms" | "players"
        self.selected_room_id: str | None = None
        self.scroll = 0

        self.running = True
        self._buttons: list[Button] = []

    # -- vòng lặp chính -----------------------------------------------------
    def run(self):
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(FPS)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = max(0, self.scroll - event.y * 20)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self._buttons:
                    if btn.hit(event.pos):
                        btn.on_click(btn.data)
                        break

    # -- vẽ toàn bộ khung hình -----------------------------------------------
    def _draw(self):
        self.screen.fill(COL_BG)
        self._buttons.clear()

        w, h = self.screen.get_size()
        self._draw_header(w)
        self._draw_sidebar(0, 60, SIDEBAR_W, h - 60)
        self._draw_main(SIDEBAR_W, 60, w - SIDEBAR_W, h - 60)

        pygame.display.flip()

    # -- header ---------------------------------------------------------------
    def _draw_header(self, w):
        pygame.draw.rect(self.screen, COL_PANEL_ALT, (0, 0, w, 60))
        pygame.draw.line(self.screen, COL_BORDER, (0, 60), (w, 60))
        draw_text(self.screen, self.font_title, "Caro Server", (20, 16), COL_TEXT)

        players = _snapshot_players(self.player_manager)
        rooms = _snapshot_rooms(self.room_manager)
        playing = sum(1 for r in rooms if _enum_val(r.status) == "playing")
        info = f"{len(players)} client   |   {len(rooms)} ban co   |   {playing} dang dau"
        draw_text(self.screen, self.font, info, (w - 20 - self.font.size(info)[0], 21), COL_TEXT_DIM)

    # -- sidebar: tab Rooms / Players ------------------------------------------
    def _draw_sidebar(self, x, y, w, h):
        pygame.draw.rect(self.screen, COL_PANEL, (x, y, w, h))
        pygame.draw.line(self.screen, COL_BORDER, (x + w, y), (x + w, y + h))

        # tabs
        tab_h = 40
        rooms_rect = (x, y, w // 2, tab_h)
        players_rect = (x + w // 2, y, w // 2, tab_h)

        def set_tab(name):
            self.tab = name
            self.scroll = 0

        for rect, name, label in ((rooms_rect, "rooms", "Ban co"), (players_rect, "players", "Client")):
            active = self.tab == name
            pygame.draw.rect(self.screen, COL_SELECTED if active else COL_PANEL, rect)
            color = COL_ACCENT if active else COL_TEXT_DIM
            tw = self.font_bold.size(label)[0]
            draw_text(self.screen, self.font_bold, label, (rect[0] + (rect[2] - tw) // 2, rect[1] + 10), color)
            self._buttons.append(Button(rect, lambda _n, n=name: set_tab(n)))
        pygame.draw.line(self.screen, COL_BORDER, (x, y + tab_h), (x + w, y + tab_h))

        list_top = y + tab_h
        if self.tab == "rooms":
            self._draw_room_list(x, list_top, w, h - tab_h)
        else:
            self._draw_player_list(x, list_top, w, h - tab_h)

    def _draw_room_list(self, x, y, w, h):
        rooms = _snapshot_rooms(self.room_manager)
        rooms.sort(key=lambda r: r.created_at, reverse=True)

        row_h = 64
        cy = y - self.scroll
        for room in rooms:
            if cy + row_h > y and cy < y + h:
                self._draw_room_row(x, cy, w, row_h, room)
            cy += row_h

        if not rooms:
            draw_text(self.screen, self.font_small, "Chua co ban co nao.", (x + 16, y + 16), COL_TEXT_DIM)

    def _draw_room_row(self, x, y, w, row_h, room):
        rect = pygame.Rect(x, y, w, row_h)
        selected = room.room_id == self.selected_room_id
        pygame.draw.rect(self.screen, COL_SELECTED if selected else COL_PANEL, rect)
        pygame.draw.line(self.screen, COL_BORDER, (x, y + row_h), (x + w, y + row_h))

        draw_text(self.screen, self.font_bold, f"#{room.room_id}", (x + 14, y + 8), COL_TEXT)

        status = _enum_val(room.status)
        draw_text(
            self.screen, self.font_small, status.upper(), (x + w - 90, y + 10), STATUS_COLOR.get(status, COL_TEXT_DIM)
        )

        vs = f"X: {room.player_x}   O: {room.player_o}"
        draw_text(self.screen, self.font_small, vs, (x + 14, y + 32), COL_TEXT_DIM, max_w=w - 100)

        spec = f"{len(room.spectators)} khan gia"
        draw_text(self.screen, self.font_small, spec, (x + 14, y + 48), COL_TEXT_DIM)

        self._buttons.append(Button(rect, self._select_room, data=room.room_id))

    def _select_room(self, room_id):
        self.selected_room_id = room_id

    def _draw_player_list(self, x, y, w, h):
        players = _snapshot_players(self.player_manager)
        players.sort(key=lambda p: p.connected_at, reverse=True)

        row_h = 56
        cy = y - self.scroll
        for p in players:
            if cy + row_h > y and cy < y + h:
                self._draw_player_row(x, cy, w, row_h, p)
            cy += row_h

        if not players:
            draw_text(self.screen, self.font_small, "Chua co client nao ket noi.", (x + 16, y + 16), COL_TEXT_DIM)

    def _draw_player_row(self, x, y, w, row_h, player):
        rect = pygame.Rect(x, y, w, row_h)
        pygame.draw.rect(self.screen, COL_PANEL, rect)
        pygame.draw.line(self.screen, COL_BORDER, (x, y + row_h), (x + w, y + row_h))

        draw_text(
            self.screen, self.font_bold, player.username or player.player_id, (x + 14, y + 6), COL_TEXT, max_w=w - 30
        )

        status = _enum_val(player.status)
        pygame.draw.circle(self.screen, STATUS_COLOR.get(status, COL_TEXT_DIM), (x + 20, y + 34), 5)
        draw_text(self.screen, self.font_small, status, (x + 32, y + 28), COL_TEXT_DIM)

        room_txt = f"phong: {player.current_room_id}" if player.current_room_id else "chua vao phong"
        draw_text(self.screen, self.font_small, room_txt, (x + w // 2, y + 28), COL_TEXT_DIM, max_w=w // 2 - 16)

        # click vào 1 player -> nếu đang trong phòng, nhảy qua tab Rooms và chọn phòng đó
        if player.current_room_id:
            self._buttons.append(Button(rect, self._jump_to_room, data=player.current_room_id))

    def _jump_to_room(self, room_id):
        self.tab = "rooms"
        self.selected_room_id = room_id
        self.scroll = 0

    # -- panel chính: chi tiết bàn cờ đang chọn --------------------------------
    def _draw_main(self, x, y, w, h):
        pygame.draw.rect(self.screen, COL_BG, (x, y, w, h))

        room = None
        if self.selected_room_id:
            room = self.room_manager.get_room(self.selected_room_id)

        if room is None:
            msg = "Chon 1 ban co ben trai de xem chi tiet"
            tw = self.font.size(msg)[0]
            draw_text(self.screen, self.font, msg, (x + (w - tw) // 2, y + h // 2), COL_TEXT_DIM)
            return

        # info bar
        pad = 20
        draw_text(self.screen, self.font_bold, f"Phong #{room.room_id}", (x + pad, y + pad), COL_TEXT)
        status = _enum_val(room.status)
        draw_text(
            self.screen, self.font, status.upper(), (x + pad, y + pad + 28), STATUS_COLOR.get(status, COL_TEXT_DIM)
        )
        draw_text(
            self.screen,
            self.font,
            f"X = {room.player_x}      O = {room.player_o}      Khan gia: {len(room.spectators)}",
            (x + pad + 110, y + pad + 28),
            COL_TEXT_DIM,
        )

        board_top = y + pad + 64
        board_area_h = h - (board_top - y) - pad
        self._draw_board(x + pad, board_top, w - 2 * pad, board_area_h, room.board_instance)

    def _draw_board(self, x, y, w, h, board):
        if board is None:
            draw_text(self.screen, self.font, "Ban co chua duoc khoi tao.", (x, y), COL_TEXT_DIM)
            return

        rows, cols = board.rows, board.cols
        cell = min(w // cols, h // rows)
        board_w, board_h = cell * cols, cell * rows
        ox = x + (w - board_w) // 2
        oy = y

        pygame.draw.rect(self.screen, COL_PANEL, (ox, oy, board_w, board_h))
        for i in range(rows + 1):
            pygame.draw.line(self.screen, COL_GRID, (ox, oy + i * cell), (ox + board_w, oy + i * cell))
        for j in range(cols + 1):
            pygame.draw.line(self.screen, COL_GRID, (ox + j * cell, oy), (ox + j * cell, oy + board_h))

        last = board.last_move[-1] if board.last_move else None
        for r in range(rows):
            for c in range(cols):
                v = board.grid[r][c]
                if v == ".":
                    continue
                cx = ox + c * cell + cell // 2
                cy = oy + r * cell + cell // 2
                margin = max(4, cell // 6)
                if last == (r, c):
                    pygame.draw.rect(self.screen, COL_SELECTED, (ox + c * cell, oy + r * cell, cell, cell))
                if v == "X":
                    pygame.draw.line(
                        self.screen,
                        COL_X,
                        (ox + c * cell + margin, oy + r * cell + margin),
                        (ox + (c + 1) * cell - margin, oy + (r + 1) * cell - margin),
                        3,
                    )
                    pygame.draw.line(
                        self.screen,
                        COL_X,
                        (ox + (c + 1) * cell - margin, oy + r * cell + margin),
                        (ox + c * cell + margin, oy + (r + 1) * cell - margin),
                        3,
                    )
                else:
                    pygame.draw.circle(self.screen, COL_O, (cx, cy), cell // 2 - margin, 3)


def run_dashboard(player_manager, room_manager):
    ServerDashboard(player_manager, room_manager).run()


# ----------------------------------------------------------------------------
# DEMO: dữ liệu giả để xem trước UI mà không cần server thật
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")

    # Fake Caro board (giống class Caro bạn đưa, thu gọn) để demo hiển thị
    class FakeCaro:
        def __init__(self, rows=10, cols=10):
            self.rows, self.cols = rows, cols
            self.grid = [["." for _ in range(cols)] for _ in range(rows)]
            self.last_move = []

        def random_move(self):
            empties = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == "."]
            if not empties:
                return
            r, c = random.choice(empties)
            self.grid[r][c] = "X" if len(self.last_move) % 2 == 0 else "O"
            self.last_move.append((r, c))

    from enum import Enum

    class PlayerStatus(Enum):
        IDLE = "idle"
        PLAYING = "playing"
        SPECTATING = "spectating"

    class RoomStatus(Enum):
        WAITING = "waiting"
        PLAYING = "playing"
        FINISHED = "finished"

    @dataclass
    class FakePlayer:
        player_id: str
        username: str
        connection: object = None
        status: PlayerStatus = PlayerStatus.IDLE
        current_room_id: str | None = None
        connected_at: float = field(default_factory=time.time)

    @dataclass
    class FakeRoom:
        room_id: str
        player_x: str
        player_o: str
        status: RoomStatus = RoomStatus.WAITING
        board_instance: FakeCaro | None = None
        spectators: set = field(default_factory=set)
        created_at: float = field(default_factory=time.time)

    class FakeManager:
        """Mô phỏng PlayerManager + RoomManager để demo, cùng interface (_lock, _players/_rooms)."""

        def __init__(self):
            self._lock = threading.Lock()
            self._players: dict[str, FakePlayer] = {}
            self._rooms: dict[str, FakeRoom] = {}

        def get_room(self, room_id):
            with self._lock:
                return self._rooms.get(room_id)

    mgr_players = FakeManager()
    mgr_rooms = FakeManager()

    def seed_fake_data():
        names = ["An", "Binh", "Chi", "Duc", "Em", "Phong", "Giang", "Hoa"]
        for i, name in enumerate(names):
            pid = f"p{i}"
            mgr_players._players[pid] = FakePlayer(
                player_id=pid, username=name, status=random.choice(list(PlayerStatus))
            )

        pids = list(mgr_players._players.keys())
        for i in range(3):
            rid = str(uuid.uuid4())[:8]
            px, po = random.sample(pids, 2)
            board = FakeCaro()
            for _ in range(random.randint(0, 15)):
                board.random_move()
            mgr_rooms._rooms[rid] = FakeRoom(
                room_id=rid, player_x=px, player_o=po, status=RoomStatus.PLAYING, board_instance=board
            )
            mgr_players._players[px].status = PlayerStatus.PLAYING
            mgr_players._players[px].current_room_id = rid
            mgr_players._players[po].status = PlayerStatus.PLAYING
            mgr_players._players[po].current_room_id = rid

    seed_fake_data()

    def background_moves():
        while True:
            time.sleep(1.2)
            with mgr_rooms._lock:
                rooms = list(mgr_rooms._rooms.values())
            if rooms:
                r = random.choice(rooms)
                if r.board_instance:
                    r.board_instance.random_move()

    threading.Thread(target=background_moves, daemon=True).start()

    run_dashboard(mgr_players, mgr_rooms)
