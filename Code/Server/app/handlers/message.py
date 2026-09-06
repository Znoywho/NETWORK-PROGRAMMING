"""Application-level WebSocket message routing for Caro."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import bcrypt
from app.db import session
from app.game.caro import Caro
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.models.matchmaking_models import PlayerStatus, Room, RoomStatus
from app.models.user import User

BOARD_ROWS = 15
BOARD_COLS = 15
WINNING_CONDITION = 5


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
        *,
        db_session=None,
        board_factory: Callable[[], Caro] | None = None,
    ):
        self.pm = player_manager
        self.rm = room_manager
        self.im = invite_manager
        self.session = db_session if db_session is not None else session
        self.board_factory = board_factory or self._new_board

    def handle(self, message: object, websocket: object) -> list[dict[str, Any]]:
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
            return self._login_handler(message, websocket)

        if message_type == "create_user":
            return self._create_user_hanlder(message, websocket)

        player_id = self._find_id_by_ws(websocket)
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

    def disconnect(self, websocket: object) -> list[dict[str, Any]]:
        """Remove a disconnected player and notify affected connected clients."""
        player_id = self._find_id_by_ws(websocket)
        if player_id is None:
            return []

        deliveries: list[dict[str, Any]] = []
        player = self.pm.get_player(player_id)
        room = self.rm.get_room(player.current_room_id) if (player and player.current_room_id) else None
        if room and player_id in (room.player_x, room.player_o) and room.status == RoomStatus.PLAYING:
            opponent_id = room.player_o if player_id == room.player_x else room.player_x
            room.status = RoomStatus.FINISHED
            self._set_player_idle(opponent_id)
            for spectator_id in room.spectators:
                self._set_player_idle(spectator_id)

            recipients = self._room_recipients(room, exclude={player_id})
            if recipients:
                deliveries.extend(
                    self._game_result_deliveries(room.room_id, opponent_id, [room.player_x, room.player_o])
                )
        elif room and player_id in room.spectators:
            self.rm.remove_spectator(room.room_id, player_id)

        self.pm.remove_player(player_id)
        deliveries.append(self._broadcast_online_players())
        return deliveries

    def _login_handler(self, message: dict[str, Any], websocket: object) -> list[dict[str, Any]]:
        username = message.get("username")
        password = message.get("password")
        if not isinstance(username, str) or not username.strip():
            return [self._error("INVALID_MESSAGE", "username is required.")]
        if not isinstance(password, str):
            return [self._error("INVALID_MESSAGE", "password is required.")]

        current_player_id = self._find_id_by_ws(websocket)
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
        if existing_player is not None and existing_player.connection is not websocket:
            return [self._error("ALREADY_ONLINE", "This user is already online.")]

        user.last_login_at = datetime.now()
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            return [self._error("DATABASE_ERROR", "Could not complete login.")]
        self.pm.add_player(player_id, user.username, websocket)

        return [
            self._reply({
                "type": "login", 
                "username": user.username, 
                "playerId": player_id
                }),
            self._broadcast_online_players(),
        ]


    def _create_user_hanlder(self, message, websocket):
        user = self._check_user(message.get("username").strip())
        if user is not None:
            return [self._error("USER_ALREADY_EXIST", "This user already exist")]
        hashed_password = hash_password(message.get("password"))

        user = User(
                username = message.get("username"),
                password_hash = hashed_password,
                last_login_at = datetime.now()
                )

        self.session.add(user)
        
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            return [self._error("DATABASE_ERROR", "Could not complete login.")]

        return [
            self._reply({
                "type": "create_user",
                "username": user.username,
                "playerId": user.id
                }),
            self._broadcast_online_players(),
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

        result = self.im.accept_invite(invite_id, self.board_factory)
        if not result["success"]:
            return [self._error("INVITE_NOT_FOUND", result["reason"])]

        room = self.rm.get_room(result["room_id"])
        if room is None or room.board_instance is None:
            return [self._error("ROOM_ERROR", "Could not create a game room.")]
        room.status = RoomStatus.PLAYING

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
        recipients = self._room_recipients(room)
        winner = board._get_winner()
        if winner == -1:
            return [self._targeted(recipients, self._game_state(room))]

        room.status = RoomStatus.FINISHED
        winner_id = room.player_x if winner == 0 else room.player_o if winner == 1 else None
        for room_player_id in (room.player_x, room.player_o):
            self._set_player_idle(room_player_id)
        for spectator_id in room.spectators:
            self._set_player_idle(spectator_id)

        return [
            self._targeted(recipients, self._game_state(room, winner_id or player_id)),
            *self._game_result_deliveries(room.room_id, winner_id, [room.player_x, room.player_o]),
            self._broadcast_online_players(),
        ]

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

        opponent_id = room.player_o if player_id == room.player_x else room.player_x
        recipients = self._room_recipients(room)
        room.status = RoomStatus.FINISHED
        for room_player_id in (room.player_x, room.player_o):
            self._set_player_idle(room_player_id)
        for spectator_id in room.spectators:
            self._set_player_idle(spectator_id)

        return [
            self._reply({"type": "leave_room_result", "success": True, "role": "player", "winnerId": opponent_id}),
            self._targeted(recipients, self._game_state(room, opponent_id)),
            *self._game_result_deliveries(room.room_id, opponent_id, [room.player_x, room.player_o]),
            self._broadcast_online_players(),
        ]

    def _check_user(self, username: str) -> User | None:
        return self.session.query(User).filter(User.username == username).first()

    def _list_online_players(self) -> list[dict[str, str]]:
        return [
            {"playerId": info["player_id"], "username": info["user_name"], "status": info["status"]}
            for info in self.pm.list_online()
        ]

    def _find_id_by_ws(self, websocket: object) -> str | None:
        for info in self.pm.list_online():
            player = self.pm.get_player(info["player_id"])
            if player is not None and player.connection is websocket:
                return player.player_id
        return None

    def _new_board(self) -> Caro:
        return Caro(BOARD_ROWS, BOARD_COLS, WINNING_CONDITION)

    def _game_state(self, room: Room, current_player_id: str | None = None) -> dict[str, Any]:
        board = room.board_instance
        if board is None:
            raise ValueError("Room has no game board.")
        if current_player_id is None:
            current_player_id = room.get_player_id_by_turn(board.turn)
        return {
            "type": "game_state",
            "room_id": room.room_id,
            "board": [[0 if cell == "." else 1 if cell == "X" else 2 for cell in row] for row in board.grid],
            "currentPlayerId": current_player_id or room.player_x,
            "status": room.status.value,
        }

    def _game_result_deliveries(
        self, room_id: str, winner_id: str | None, recipients: list[str]
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
