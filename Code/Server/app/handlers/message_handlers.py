"""Application-level socket  message routing for Caro."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import bcrypt

from app.db import session
from app.game.caro import Caro
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.models.matchmaking_models import PlayerStatus, Room, RoomStatus
from app.models.match import Match
from app.models.user import User
from app.queue.db_queue import Op, db_queue

BOARD_ROWS = 15
BOARD_COLS = 15
WINNING_CONDITION = 5
K = 32

# Luat nhom cong bo cho hai dong ho duoi day:
#
#   - Het gio suy nghi cua mot luot  -> nguoi dang toi luot bi xu THUA.
#   - Mat ket noi giua van           -> van duoc giu nguyen trong
#     RECONNECT_GRACE_SECONDS giay; quay lai kip thi danh tiep, qua han
#     thi doi thu duoc xu THANG.
#
# Dong ho suy nghi bi TAM DUNG trong luc cho ket noi lai, va duoc cap
# lai tron ven khi nguoi choi tro ve — neu khong, mang chap chon se an
# mat luot cua ho hai lan.
TURN_TIME_LIMIT_SECONDS = 30
RECONNECT_GRACE_SECONDS = 60

logger = logging.getLogger(__name__)


def as_db_id(value: object) -> int | None:
    """playerId/room_id di qua JSON la chuoi, con khoa chinh trong DB la BIGINT.

    Giao thuc voi client giu nguyen kieu chuoi (GameMessages.cs khai bao
    PlayerId/MatchId la `string`), nen viec doi kieu chi xay ra ngay sat
    bien gioi database.
    """
    return int(value) if value is not None else None


def hash_password(password: str) -> str:
    """Return a bcrypt hash suitable for storing in ``users.password_hash``."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verify a password, including a malformed legacy hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (AttributeError, TypeError, ValueError):
        return False


class MessageHandler:
    """Translate client messages into delivery instructions for the server.

    A delivery has the shape ``{"targets": ..., "payload": ...}``:

    * ``targets is None`` broadcasts to all online players.
    * A non-empty target list sends to those player IDs.
    * An empty target list replies only to the socket that sent the request.

    The last case avoids broadcasting authentication and validation errors before a
    socket is associated with a player ID.
    """

    def __init__(
        self,
        player_manager: PlayerManager,
        room_manager: RoomManager,
        invite_manager: InviteManager,
        db_session=None,
        write_queue=None,
        board_factory: Callable[[], Caro] | None = None,
        clock: Callable[[], float] | None = None,
    ):
        self.pm = player_manager
        self.rm = room_manager
        self.im = invite_manager
        self.session = db_session if db_session is not None else session
        self.write_queue = write_queue if write_queue is not None else db_queue
        self.board_factory = board_factory or self._new_board
        # Tiem duoc tu ngoai vao de test khong phai ngoi cho het 30 giay that.
        self.clock = clock or time.monotonic
        # player_id -> room_id cua nguoi dang mat ket noi va con han quay lai.
        self._awaiting_reconnect: dict[str, str] = {}

    def handle(self, message: object, sock: object) -> list[dict[str, Any]]:
        """Handle one decoded client message without performing socket I/O."""
        if not isinstance(message, dict):
            return [
                    self._error("INVALID_MESSAGE", "Message must be a JSON object.")
                    ]

        message_type = message.get("type")
        if not isinstance(message_type, str):
            return [
                    self._error("INVALID_MESSAGE", "Message type is required.")
                    ]

        if message_type == "login":
            return self._login_handler(message, sock)

        if message_type == "create_user":
            return self._create_user_hanlder(message, sock)

        player_id = self._find_id_by_sock(sock)
        if player_id is None:
            return [
                    self._error("UNAUTHENTICATED",
                                "Login is required for this action.")
                    ]

        handlers = {
            "online_players": self._online_players_handler,
            "invite": self._invite_handler,
            "accept_invite": self._accept_invite_handler,
            "reject_invite": self._reject_invite_handler,
            "make_move": self._make_move_handler,
            "match_list": self._match_list_handler,
            "spectate": self._spectate_handler,
            "leave_room": self._leave_room_handler,
        }
        handler = handlers.get(message_type)
        if handler is None:
            return [
                    self._error("UNKNOWN_MESSAGE_TYPE",
                                f"Unsupported message type: {message_type}.")
                    ]

        try:
            return handler(player_id, message)
        except (KeyError, TypeError, ValueError) as exc:
            return [
                    self._error("INVALID_MESSAGE", 
                                str(exc) or "Invalid message payload.")
                    ]

    def disconnect(self, sock: object) -> list[dict[str, Any]]:
        """Xu ly mot socket vua dut.

        Nguoi choi dang trong van KHONG bi xu thua ngay: phong duoc giu
        nguyen, dong ho suy nghi tam dung, va ho co
        ``RECONNECT_GRACE_SECONDS`` giay de dang nhap lai. Qua han thi
        ``tick()`` moi ket thuc van.
        """
        player_id = self._find_id_by_sock(sock)
        if player_id is None:
            return []

        deliveries: list[dict[str, Any]] = []
        player = self.pm.get_player(player_id)
        room = self.rm.get_room(player.current_room_id) if (player and player.current_room_id) else None
        if room and player_id in (room.player_x, room.player_o) and room.status == RoomStatus.PLAYING:
            if room.disconnected_player is not None and room.disconnected_player != player_id:
                # Ca hai cung mat ket noi thi khong con ai de xu thang.
                self.pm.remove_player(player_id)
                return self._end_game_deliveries(room, None, reason="disconnect")

            room.disconnected_player = player_id
            room.reconnect_deadline = self.clock() + RECONNECT_GRACE_SECONDS
            room.turn_deadline = None  # tam dung dong ho suy nghi
            self._awaiting_reconnect[player_id] = room.room_id

            recipients = self._room_recipients(room, exclude={player_id})
            if recipients:
                deliveries.append(
                    self._targeted(
                        recipients,
                        {
                            "type": "player_disconnected",
                            "room_id": room.room_id,
                            "playerId": player_id,
                            "reconnectTimeLeft": RECONNECT_GRACE_SECONDS,
                        },
                    )
                )
        elif room and player_id in room.spectators:
            self.rm.remove_spectator(room.room_id, player_id)

        self.pm.remove_player(player_id)
        deliveries.append(self._broadcast_online_players())
        return deliveries

    def tick(self) -> list[dict[str, Any]]:
        """Kiem tra dong ho cua moi phong; server goi moi vong lap selector.

        Day la cho duy nhat thoi gian troi qua tro thanh mot su kien: het
        gio suy nghi hoac het han cho ket noi lai deu ket thuc van dau ma
        khong can client gui gi len.
        """
        now = self.clock()
        deliveries: list[dict[str, Any]] = []

        for room in self.rm.list_rooms():
            if room.status != RoomStatus.PLAYING or room.board_instance is None:
                continue

            if room.reconnect_deadline is not None:
                if now >= room.reconnect_deadline:
                    winner_id = self._opponent_of(room, room.disconnected_player)
                    deliveries.extend(
                        self._end_game_deliveries(room, winner_id, reason="disconnect")
                    )
                continue  # dong ho suy nghi dang tam dung

            if room.turn_deadline is not None and now >= room.turn_deadline:
                loser_id = room.get_player_id_by_turn(room.board_instance.turn)
                winner_id = self._opponent_of(room, loser_id)
                deliveries.extend(self._end_game_deliveries(room, winner_id, reason="timeout"))

        return deliveries

    def _login_handler(self, message: dict[str, Any], sock: object) -> list[dict[str, Any]]:
        username = message.get("username")
        password = message.get("password")
        if not isinstance(username, str) or not username.strip():
            return [self._error("INVALID_MESSAGE", "username is required.")]
        if not isinstance(password, str):
            return [self._error("INVALID_MESSAGE", "password is required.")]

        current_player_id = self._find_id_by_sock(sock)
        # Avoid duplicated player_id
        if current_player_id is not None:
            return [self._error("ALREADY_AUTHENTICATED", "This connection is already logged in.")]

        user = self._check_user(username.strip())
        if user is None:
            return [self._error("USER_NOT_EXIST", "User does not exist.")]
        if not verify_password(password, user.password_hash):
            return [self._error("WRONG_PASSWORD", "Incorrect password.")]

        player_id = str(user.id)
        existing_player = self.pm.get_player(player_id)
        if existing_player is not None and existing_player.connection is not sock:
            return [self._error("ALREADY_ONLINE", "This user is already online.")]

        user.last_login_at = datetime.now()
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            return [self._error("DATABASE_ERROR", "Could not complete login.")]
        # NOTE: Register user
        self.pm.add_player(player_id, user.username, sock)

        return [
            self._reply({
                "type": "login", 
                "username": user.username, 
                "playerId": player_id
                }),
            *self._resume_after_reconnect(player_id),
            self._broadcast_online_players(),
        ]

    def _resume_after_reconnect(self, player_id: str) -> list[dict[str, Any]]:
        """Dua nguoi vua dang nhap lai ve dung van ho dang bo do.

        Tra ve danh sach rong neu ho khong cho o phong nao — do la duong
        di cua moi lan dang nhap binh thuong.
        """
        room_id = self._awaiting_reconnect.pop(player_id, None)
        if room_id is None:
            return []

        room = self.rm.get_room(room_id)
        if room is None or room.status != RoomStatus.PLAYING or room.disconnected_player != player_id:
            return []

        room.disconnected_player = None
        room.reconnect_deadline = None
        # Cap lai tron ven mot luot: ho vua mat ket noi chu khong phai da
        # ngoi nghi may chuc giay.
        self._start_turn(room)
        self.pm.set_status(player_id, PlayerStatus.PLAYING)
        self.pm.set_current_room(player_id, room_id)

        deliveries: list[dict[str, Any]] = []
        others = self._room_recipients(room, exclude={player_id})
        if others:
            deliveries.append(
                self._targeted(
                    others,
                    {"type": "player_reconnected", "room_id": room_id, "playerId": player_id},
                )
            )
        # Ban co day du cho ca phong, ke ca nguoi vua quay lai.
        deliveries.append(self._targeted(self._room_recipients(room), self._game_state(room)))
        return deliveries


    def _create_user_hanlder(self, message, sock):
        username = message.get("username")
        password = message.get("password")
        # Handler nay chay ngoai khoi try/except cua handle(), nen thieu field
        # ma khong kiem tra la AttributeError lam chet ca server.
        if not isinstance(username, str) or not username.strip():
            return [self._error("INVALID_MESSAGE", "username is required.")]
        if not isinstance(password, str) or len(password) < 10:
            return [self._error("INVALID_MESSAGE", "password must be at least 10 characters.")]

        username = username.strip()
        user = self._check_user(username)
        if user is not None:
            return [self._error("USER_ALREADY_EXIST", "This user already exist")]
        hashed_password = hash_password(password)

        user = User(
                username = username,
                password_hash = hashed_password,
                last_login_at = datetime.now()
                )

        self.session.add(user)
        
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            return [self._error("DATABASE_ERROR", "Could not complete create user.")]

        return [
            self._reply({
                "type": "create_user",
                "username": user.username,
                "playerId": str(user.id)
                }),
            ]

        

    def changeUser(self, user: User):
        if user:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                return [self._error("DATABASE_ERROR", "Could not change information of user.")]
        else:
                return [self._error("DATABASE_ERROR", "Could not change information of user.")]
        return [
            self._reply({
                "type": "create_user",
                "username": user.username,
                "playerId": str(user.id)
                }),
            ]

    def _online_players_handler(self, _player_id: str, _message: dict[str, Any]) -> list[dict[str, Any]]:
        return [
                self._reply({
                    "type": "online_players", 
                    "players": self._list_online_players()
                    })
                ]

    def _invite_handler(self, from_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        to_id = message.get("toPlayerId")
        invite_id = message.get("inviteId")
        if not isinstance(to_id, str) or not to_id:
            return [self._error("INVALID_MESSAGE", "toPlayerId is required.")]
        if not isinstance(invite_id, str) or not invite_id:
            return [self._error("INVALID_MESSAGE", "inviteId is required.")]
        if to_id == from_id:
            return [self._error("INVALID_INVITE", "You cannot invite yourself.")]

        result = self.im.send_invite(from_id, to_id, invite_id)
        if not result["success"]:
            return [self._error("INVITE_REJECTED", result["reason"])]

        sender = self.pm.get_player(from_id)
        return [
            self._reply({"type": "invite_result", "success": True, "inviteId": invite_id, "toPlayerId": to_id}),
            self._targeted(
                [to_id],
                {
                    "type": "invite",
                    "inviteId": invite_id,
                    "fromPlayerId": from_id,
                    "fromUsername": sender.username if sender else from_id,
                },
            ),
        ]

    def _accept_invite_handler(self, player_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        invite_id = message.get("inviteId")
        if not isinstance(invite_id, str) or not invite_id:
            return [self._error("INVALID_MESSAGE", "inviteId is required.")]

        invite = self.im.get_invite(invite_id)
        if invite is None:
            return [self._error("INVITE_NOT_FOUND", "Invite was not found or has expired.")]
        if invite["to"] != player_id:
            return [self._error("FORBIDDEN", "Only the invited player can accept this invite.")]
        if not self.pm.is_online(invite["from"]):
            self.im.reject_invite(invite_id)
            return [self._error("INVITER_OFFLINE", "The inviting player is no longer online.")]

        # Tao hang `matches` TRUOC, dong bo, de lay id do Postgres cap lam
        # room_id. Khac voi moves/ket qua (di qua hang doi), buoc nay phai
        # dong bo vi ca van dau phu thuoc vao id nay — va no chi chay mot
        # lan moi van nen khong lam nghen vong lap selector dang ke.
        match_id = self._create_match_row(invite["from"], invite["to"])
        if match_id is None:
            return [self._error("DATABASE_ERROR", "Could not create the match record.")]

        result = self.im.accept_invite(invite_id, self.board_factory, str(match_id))
        if not result["success"]:
            return [self._error("INVITE_NOT_FOUND", result["reason"])]

        room = self.rm.get_room(result["room_id"])
        if room is None or room.board_instance is None:
            return [self._error("ROOM_ERROR", "Could not create a game room.")]
        room.status = RoomStatus.PLAYING
        self._start_turn(room)

        return [self._targeted(self._room_recipients(room), self._game_state(room))]

    def _reject_invite_handler(self, player_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        invite_id = message.get("inviteId")
        if not isinstance(invite_id, str) or not invite_id:
            return [self._error("INVALID_MESSAGE", "inviteId is required.")]

        invite = self.im.get_invite(invite_id)
        if invite is None:
            return [self._error("INVITE_NOT_FOUND", "Invite was not found or has expired.")]
        if invite["to"] != player_id:
            return [self._error("FORBIDDEN", "Only the invited player can reject this invite.")]

        result = self.im.reject_invite(invite_id)
        return [
            self._reply({"type": "reject_invite_result", **result}),
            self._targeted(
                [invite["from"]], {"type": "invite_rejected", "inviteId": invite_id, "byPlayerId": player_id}
            ),
        ]

    def _make_move_handler(self, player_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        claimed_player_id = message.get("playerId")
        if not isinstance(claimed_player_id, str) or not claimed_player_id:
            return [self._error("INVALID_MESSAGE", "playerId is required.")]
        if claimed_player_id != player_id:
            return [self._error("FORBIDDEN", "playerId does not match this connection.")]

        room_id = message.get("room_id")
        row = message.get("row")
        col = message.get("col")
        if not isinstance(room_id, str) or not room_id:
            return [self._error("INVALID_MESSAGE", "room_id is required.")]
        if isinstance(row, bool) or not isinstance(row, int) or isinstance(col, bool) or not isinstance(col, int):
            return [self._error("INVALID_MESSAGE", "row and col must be integers.")]

        room = self.rm.get_room(room_id)
        if room is None or room.board_instance is None:
            return [self._error("ROOM_NOT_FOUND", "Game room was not found.")]
        if room.status != RoomStatus.PLAYING:
            return [self._error("GAME_NOT_ACTIVE", "This game is not active.")]
        if player_id not in (room.player_x, room.player_o):
            return [self._error("FORBIDDEN", "Spectators cannot make moves.")]

        board = room.board_instance
        expected_player_id = room.get_player_id_by_turn(board.turn)
        if expected_player_id != player_id:
            return [self._error("NOT_YOUR_TURN", "It is not your turn.")]
        if not 0 <= row < board.rows or not 0 <= col < board.cols:
            return [self._error("MOVE_OUT_OF_BOUNDS", "Move is outside the board.")]
        if board.grid[row][col] != ".":
            return [self._error("CELL_OCCUPIED", "That cell is already occupied.")]

        board._make_move(row, col)
        # last_move da gom ca nuoc vua danh, nen do dai chinh la move_index
        # (bat dau tu 1, so le la luot X).
        self._persist_move(room, player_id, row, col, len(board.last_move))

        winner = board._get_winner()
        if winner == -1:
            # Nuoc di hop le nap lai dong ho cho doi thu.
            self._start_turn(room)
            return [self._targeted(self._room_recipients(room), self._game_state(room))]

        # score_player doi phong da o trang thai FINISHED moi chiu tinh diem.
        room.status = RoomStatus.FINISHED
        self.score_player(room, winner)
        winner_id = room.player_x if winner == 0 else room.player_o if winner == 1 else None
        return self._end_game_deliveries(room, winner_id, drawn=winner == 2)


    def score_player(self, room: Room, winner: int):
        if room.status != RoomStatus.FINISHED:
            return [self._error("ROOM_NOT_FINISHED", "Game room was not finished.")]

        player_x_user = self.session.query(User).filter(User.id == as_db_id(room.player_x)).first()
        player_o_user = self.session.query(User).filter(User.id == as_db_id(room.player_o)).first()

        if player_x_user is None or player_o_user is None:
            return [self._error(code="USER_NOT_FOUND", message="Player user not found.")]

        E_X = 1 / (1 + 10 ** ((player_o_user.ranking - player_x_user.ranking) / 400))
        E_O = 1 / (1 + 10 ** ((player_x_user.ranking - player_o_user.ranking) / 400))

        if winner == 0:      
            S_X, S_O = 1, 0
        elif winner == 1:    
            S_X, S_O = 0, 1
        else:                
            S_X, S_O = 0.5, 0.5

        player_x_user.ranking += int(K * (S_X - E_X))
        player_o_user.ranking += int(K * (S_O - E_O))

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Scoring failed for room {room.room_id}: {e}")

    # ------------------------------------------------------------
    #  Ghi lich su van dau (matches / moves)
    #
    #  Mo van: ghi DONG BO (_create_match_row), vi room_id chinh la id
    #  Postgres cap. Mot lan moi van nen chi phi khong dang ke.
    #
    #  Nuoc di va ket qua: di qua DBQueue. Handler chi day event roi tra
    #  ve ngay, DB Writer o thread rieng moi la ben commit. Day la duong
    #  ghi day dac nhat, su co database khong duoc lam gian doan van dau.
    # ------------------------------------------------------------
    def _enqueue(self, op: str, data: dict[str, Any]) -> None:
        try:
            self.write_queue.put(op, data)
        except Exception:
            logger.exception("Khong the day event %s vao hang doi ghi DB", op)

    def _create_match_row(self, player_x_id: str, player_o_id: str) -> int | None:
        """INSERT mot van moi va tra ve id Postgres vua cap, None neu that bai.

        Day la duong ghi DB dong bo duy nhat trong luong van dau. Doi lai,
        hang `matches` chac chan ton tai truoc moi `moves` tro toi no, nen
        rang buoc khoa ngoai duoc bao dam boi cau truc chu khong phai nho
        thu tu FIFO cua hang doi.
        """
        match = Match(
            player_x_id=as_db_id(player_x_id),
            player_o_id=as_db_id(player_o_id),
            status=RoomStatus.PLAYING.value,
            board_rows=BOARD_ROWS,
            board_cols=BOARD_COLS,
            win_condition=WINNING_CONDITION,
            started_at=datetime.now(timezone.utc),
        )
        try:
            self.session.add(match)
            # flush de lay id ngay (INSERT ... RETURNING), commit sau.
            self.session.flush()
            match_id = match.id
            self.session.commit()
            return match_id
        except Exception:
            self.session.rollback()
            logger.exception("Khong tao duoc hang matches cho %s vs %s", player_x_id, player_o_id)
            return None

    def _persist_move(
        self, room: Room, player_id: str, row: int, col: int, move_index: int
    ) -> None:
        self._enqueue(
            Op.INSERT_MOVE,
            {
                "match_id": room.room_id,
                "player_id": player_id,
                "row_idx": row,
                "col_idx": col,
                "move_index": move_index,
            },
        )

    def _persist_match_result(
        self, room: Room, winner_id: str | None, drawn: bool = False
    ) -> None:
        if drawn:
            result = "draw"
        elif winner_id is None:
            result = "aborted"
        else:
            result = "x_win" if winner_id == room.player_x else "o_win"

        self._enqueue(
            Op.UPDATE_MATCH_RESULT,
            {
                "match_id": room.room_id,
                "status": RoomStatus.FINISHED.value,
                "result": result,
                "winner_id": winner_id,
                "ended_at": datetime.now(timezone.utc),
            },
        )

    def _match_list_handler(self, _player_id: str, _message: dict[str, Any]) -> list[dict[str, Any]]:
        """Danh sach tran dang dien ra, de nguoi dung chon phong vao xem."""
        return [self._reply({"type": "match_list", "matches": self._list_active_matches()})]

    def _list_active_matches(self) -> list[dict[str, Any]]:
        matches = []
        for room in self.rm.list_rooms():
            if room.status != RoomStatus.PLAYING or room.board_instance is None:
                continue
            matches.append(
                {
                    "room_id": room.room_id,
                    "playerXId": room.player_x,
                    "playerXName": self._username_of(room.player_x),
                    "playerOId": room.player_o,
                    "playerOName": self._username_of(room.player_o),
                    "spectatorCount": len(room.spectators),
                    "moveCount": len(room.board_instance.last_move),
                    "turnTimeLeft": self._turn_time_left(room),
                }
            )
        return matches

    def _username_of(self, player_id: str) -> str:
        """Ten hien thi cua mot player_id, ke ca khi ho dang mat ket noi."""
        player = self.pm.get_player(player_id)
        if player is not None:
            return player.username
        try:
            user = self.session.query(User).filter(User.id == as_db_id(player_id)).first()
        except Exception:
            logger.exception("Khong tra cuu duoc username cua %s", player_id)
            return player_id
        return user.username if user else player_id

    def _spectate_handler(self, player_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        room_id = message.get("room_id")
        if not isinstance(room_id, str) or not room_id:
            return [self._error("INVALID_MESSAGE", "room_id is required.")]

        room = self.rm.get_room(room_id)
        player = self.pm.get_player(player_id)
        if room is None or room.board_instance is None:
            return [self._error("ROOM_NOT_FOUND", "Game room was not found.")]
        if player is None:
            return [self._error("UNAUTHENTICATED", "Player is no longer online.")]
        if player_id in (room.player_x, room.player_o):
            return [self._error("INVALID_SPECTATE", "Players cannot spectate their own room.")]
        if player.status == PlayerStatus.PLAYING:
            return [self._error("PLAYER_BUSY", "Leave the current game before spectating.")]

        if player.status == PlayerStatus.SPECTATING and player.current_room_id != room_id:
            self.rm.remove_spectator(player.current_room_id, player_id)

        self.rm.add_spectator(room_id, player_id)
        self.pm.set_status(player_id, PlayerStatus.SPECTATING)
        self.pm.set_current_room(player_id, room_id)
        return [self._reply(self._game_state(room)), self._broadcast_online_players()]

    def _leave_room_handler(self, player_id: str, message: dict[str, Any]) -> list[dict[str, Any]]:
        room_id = message.get("room_id")
        if not isinstance(room_id, str) or not room_id:
            return [self._error("INVALID_MESSAGE", "room_id is required.")]

        room = self.rm.get_room(room_id)
        if room is None:
            return [self._error("ROOM_NOT_FOUND", "Game room was not found.")]

        if player_id in room.spectators:
            self.rm.remove_spectator(room_id, player_id)
            self._set_player_idle(player_id)
            return [
                self._reply({"type": "leave_room_result", "success": True, "role": "spectator"}),
                self._broadcast_online_players(),
            ]

        if player_id not in (room.player_x, room.player_o):
            return [self._error("FORBIDDEN", "You are not in this room.")]

        if room.status == RoomStatus.FINISHED:
            self._set_player_idle(player_id)
            return [
                self._reply({"type": "leave_room_result", "success": True, "role": "player"}),
                self._broadcast_online_players(),
            ]

        opponent_id = self._opponent_of(room, player_id)
        return [
            self._reply({"type": "leave_room_result", "success": True, "role": "player", "winnerId": opponent_id}),
            *self._end_game_deliveries(room, opponent_id, reason="forfeit"),
        ]

    def _check_user(self, username: str) -> User | None:
        return self.session.query(User).filter(User.username == username).first()

    def _list_online_players(self) -> list[dict[str, str]]:
        return [
            {"playerId": info["player_id"], "username": info["user_name"], "status": info["status"]}
            for info in self.pm.list_online()
        ]

    def _find_id_by_sock(self, sock: object) -> str | None:
        return self.pm.find_player_by_socket(sock)

    def _new_board(self) -> Caro:
        return Caro(BOARD_ROWS, BOARD_COLS, WINNING_CONDITION)

    def _start_turn(self, room: Room) -> None:
        """Cap tron ven mot luot suy nghi cho nguoi sap di."""
        room.turn_deadline = self.clock() + TURN_TIME_LIMIT_SECONDS

    def _turn_time_left(self, room: Room) -> int:
        """So giay con lai cua luot hien tai; 0 khi dong ho khong chay."""
        if room.turn_deadline is None:
            return 0
        return max(0, int(round(room.turn_deadline - self.clock())))

    def _opponent_of(self, room: Room, player_id: str | None) -> str | None:
        if player_id == room.player_x:
            return room.player_o
        if player_id == room.player_o:
            return room.player_x
        return None

    def _end_game_deliveries(
        self,
        room: Room,
        winner_id: str | None,
        *,
        drawn: bool = False,
        reason: str | None = None,
    ) -> list[dict[str, Any]]:
        """Dong mot van: tat dong ho, ghi ket qua, tra moi nguoi ve idle.

        Moi duong ket thuc (thang binh thuong, het gio, bo tran, het han
        ket noi lai) deu di qua day nen khong duong nao quen mat mot buoc.
        """
        room.status = RoomStatus.FINISHED
        room.turn_deadline = None
        if room.disconnected_player is not None:
            self._awaiting_reconnect.pop(room.disconnected_player, None)
            room.disconnected_player = None
        room.reconnect_deadline = None

        recipients = self._room_recipients(room)
        self._persist_match_result(room, winner_id, drawn=drawn)
        for room_player_id in (room.player_x, room.player_o, *room.spectators):
            self._set_player_idle(room_player_id)

        return [
            self._targeted(recipients, self._game_state(room, winner_id)),
            *self._game_result_deliveries(
                room.room_id, winner_id, [room.player_x, room.player_o], reason=reason
            ),
            self._broadcast_online_players(),
        ]

    def _game_state(self, room: Room, current_player_id: str | None = None) -> dict[str, Any]:
        board = room.board_instance
        if board is None:
            raise ValueError("Room has no game board.")
        if current_player_id is None:
            current_player_id = room.get_player_id_by_turn(board.turn)
        payload = {
            "type": "game_state",
            "room_id": room.room_id,
            "board": [[0 if cell == "." else 1 if cell == "X" else 2 for cell in row] for row in board.grid],
            "currentPlayerId": current_player_id or room.player_x,
            "status": room.status.value,
            # Khan gia vao giua tran cung nhan duoc dong ho, khong chi ban co.
            "turnTimeLimit": TURN_TIME_LIMIT_SECONDS,
            "turnTimeLeft": self._turn_time_left(room),
        }
        if room.reconnect_deadline is not None:
            payload["waitingForPlayerId"] = room.disconnected_player
            payload["reconnectTimeLeft"] = max(
                0, int(round(room.reconnect_deadline - self.clock()))
            )
        return payload

    def _game_result_deliveries(
        self,
        room_id: str,
        winner_id: str | None,
        recipients: list[str],
        *,
        reason: str | None = None,
    ) -> list[dict[str, Any]]:
        deliveries = []
        for recipient_id in recipients:
            if winner_id is None:
                payload = {"type": "game_result", "room_id": room_id, "result": "draw"}
            else:
                payload = {
                    "type": "game_result",
                    "room_id": room_id,
                    "result": "win" if recipient_id == winner_id else "lose",
                    "winnerId": winner_id,
                }
            # timeout | disconnect | forfeit — de client noi ro vi sao van ket thuc.
            if reason is not None:
                payload["reason"] = reason
            deliveries.append(self._targeted([recipient_id], payload))
        return deliveries

    def _room_recipients(self, room: Room, *, exclude: set[str] | None = None) -> list[str]:
        excluded = exclude or set()
        return [
            player_id
            for player_id in (room.player_x, room.player_o, *room.spectators)
            if player_id not in excluded and self.pm.is_online(player_id)
        ]

    def _set_player_idle(self, player_id: str) -> None:
        self.pm.set_status(player_id, PlayerStatus.IDLE)
        self.pm.set_current_room(player_id, None)

    def _broadcast_online_players(self) -> dict[str, Any]:
        return self._broadcast({"type": "online_players", "players": self._list_online_players()})

    def _reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._targeted([], payload)

    def _targeted(self, targets: list[str], payload: dict[str, Any]) -> dict[str, Any]:
        return {"targets": targets, "payload": payload}

    def _broadcast(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"targets": None, "payload": payload}

    def _error(self, code: str, message: str) -> dict[str, Any]:
        return self._reply({"type": "error", "code": code, "message": message})
