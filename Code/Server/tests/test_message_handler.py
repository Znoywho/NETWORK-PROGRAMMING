import asyncio
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from game.caro import Caro
from handlers.message import MessageHandler, hash_password
from matchmaking.invite_manager import InviteManager
from matchmaking.player_manager import PlayerManager
from matchmaking.room_manager import RoomManager
from models.matchmaking_models import PlayerStatus, RoomStatus
from network.server import ServerHandler


class FakeQuery:
    def __init__(self, users):
        self.users = users

    def filter(self, _criterion):
        return self

    def first(self):
        return next(iter(self.users.values()), None)


class FakeSession:
    def __init__(self, users):
        self.users = users
        self.commits = 0

    def query(self, _model):
        return FakeQuery(self.users)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class FakeUser:
    def __init__(self, player_id, username, password):
        self.id = uuid.UUID(player_id)
        self.username = username
        self.password_hash = hash_password(password)
        self.last_login_at = None


class FakeSocket:
    def __init__(self):
        self.messages = []

    async def send(self, payload):
        self.messages.append(payload)


class MessageHandlerTest(unittest.TestCase):
    def setUp(self):
        self.player_manager = PlayerManager()
        self.room_manager = RoomManager()
        self.invite_manager = InviteManager(self.player_manager, self.room_manager)
        self.alice_id = "00000000-0000-0000-0000-000000000001"
        self.bob_id = "00000000-0000-0000-0000-000000000002"
        self.alice_socket = object()
        self.bob_socket = object()

    def _handler(self, *, board_factory=None):
        users = {
            "alice": FakeUser(self.alice_id, "alice", "test-password"),
            "bob": FakeUser(self.bob_id, "bob", "test-password"),
        }
        return MessageHandler(
            self.player_manager,
            self.room_manager,
            self.invite_manager,
            db_session=FakeSession(users),
            board_factory=board_factory,
        )

    def _login_both(self, handler):
        handler.session.users = {"alice": FakeUser(self.alice_id, "alice", "test-password")}
        handler.handle({"type": "login", "username": "alice", "password": "test-password"}, self.alice_socket)
        handler.session.users = {"bob": FakeUser(self.bob_id, "bob", "test-password")}
        handler.handle({"type": "login", "username": "bob", "password": "test-password"}, self.bob_socket)

    def test_login_replies_to_origin_and_broadcasts_online_players(self):
        handler = self._handler()
        result = handler.handle({"type": "login", "username": "alice", "password": "test-password"}, self.alice_socket)

        self.assertEqual([], result[0]["targets"])
        self.assertEqual("login", result[0]["payload"]["type"])
        self.assertEqual(self.alice_id, result[0]["payload"]["playerId"])
        self.assertIsNone(result[1]["targets"])
        self.assertEqual(
            [{"playerId": self.alice_id, "username": "alice", "status": "idle"}], result[1]["payload"]["players"]
        )

    def test_only_invited_player_can_accept_and_room_starts_playing(self):
        handler = self._handler()
        self._login_both(handler)

        invite_result = handler.handle(
            {"type": "invite", "inviteId": "alice-invites-bob", "toPlayerId": self.bob_id}, self.alice_socket
        )
        invite_id = invite_result[0]["payload"]["inviteId"]

        forbidden = handler.handle({"type": "accept_invite", "inviteId": invite_id}, self.alice_socket)
        self.assertEqual("FORBIDDEN", forbidden[0]["payload"]["code"])

        accepted = handler.handle({"type": "accept_invite", "inviteId": invite_id}, self.bob_socket)
        state = accepted[0]["payload"]
        room = self.room_manager.get_room(state["room_id"])
        self.assertEqual(RoomStatus.PLAYING, room.status)
        self.assertEqual({self.alice_id, self.bob_id}, set(accepted[0]["targets"]))
        self.assertEqual(self.alice_id, state["currentPlayerId"])

    def test_winning_move_sends_personal_win_and_lose_results(self):
        handler = self._handler(board_factory=lambda: Caro(1, 1, winning_condition=1))
        self._login_both(handler)
        invite_result = handler.handle(
            {"type": "invite", "inviteId": "alice-invites-bob", "toPlayerId": self.bob_id}, self.alice_socket
        )
        invite_id = invite_result[0]["payload"]["inviteId"]
        accepted = handler.handle({"type": "accept_invite", "inviteId": invite_id}, self.bob_socket)
        room_id = accepted[0]["payload"]["room_id"]

        result = handler.handle(
            {"type": "make_move", "room_id": room_id, "playerId": self.alice_id, "row": 0, "col": 0}, self.alice_socket
        )

        result_payloads = [delivery["payload"] for delivery in result if delivery["payload"]["type"] == "game_result"]
        self.assertEqual({"win", "lose"}, {payload["result"] for payload in result_payloads})
        self.assertEqual(RoomStatus.FINISHED, self.room_manager.get_room(room_id).status)
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.alice_id).status)
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.bob_id).status)

    def test_move_cannot_impersonate_another_player(self):
        handler = self._handler()
        self._login_both(handler)
        room = self.room_manager.create_room(self.alice_id, self.bob_id)
        room.board_instance = Caro(3, 3, winning_condition=3)
        room.status = RoomStatus.PLAYING

        result = handler.handle(
            {"type": "make_move", "room_id": room.room_id, "playerId": self.alice_id, "row": 0, "col": 0},
            self.bob_socket,
        )

        self.assertEqual("FORBIDDEN", result[0]["payload"]["code"])
        self.assertEqual(".", room.board_instance.grid[0][0])

    def test_server_delivery_routes_origin_targeted_and_broadcast_messages(self):
        server = ServerHandler("127.0.0.1", 0)
        origin = FakeSocket()
        other = FakeSocket()
        server.connected_users.add_player(self.alice_id, "alice", origin)
        server.connected_users.add_player(self.bob_id, "bob", other)

        asyncio.run(
            server._send_deliveries(
                [
                    {"targets": [], "payload": {"type": "origin"}},
                    {"targets": [self.bob_id], "payload": {"type": "targeted"}},
                    {"targets": None, "payload": {"type": "broadcast"}},
                ],
                origin,
            )
        )

        self.assertEqual(['{"type": "origin"}', '{"type": "broadcast"}'], origin.messages)
        self.assertEqual(['{"type": "targeted"}', '{"type": "broadcast"}'], other.messages)


if __name__ == "__main__":
    unittest.main()
