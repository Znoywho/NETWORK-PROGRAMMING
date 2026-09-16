import unittest

from app.game.caro import Caro
from app.handlers.message_handlers import MessageHandler, hash_password
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.models.matchmaking_models import PlayerStatus, RoomStatus
from app.models.match import Match
from app.network.server import ServerHandler
from app.queue.db_queue import Op


class FakeQuery:
    def __init__(self, users):
        self.users = users

    def filter(self, _criterion):
        return self

    def first(self):
        return next(iter(self.users.values()), None)


class FakeSession:
    """Thay cho Session that: cap id tang dan giong BIGSERIAL cua Postgres."""

    def __init__(self, users):
        self.users = users
        self.commits = 0
        self.added = []
        self._next_id = 1

    def query(self, _model):
        return FakeQuery(self.users)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        # Thay cho INSERT ... RETURNING id.
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id
                self._next_id += 1

    def commit(self):
        self.flush()
        self.commits += 1

    def rollback(self):
        self.added.clear()

    def added_of(self, model):
        return [obj for obj in self.added if isinstance(obj, model)]


class FakeQueue:
    """Thay cho DBQueue: chi ghi lai event de test khang dinh, khong cham DB."""

    def __init__(self):
        self.events = []

    def put(self, op, data):
        self.events.append((op, data))
        return True

    def ops(self):
        return [op for op, _ in self.events]

    def first_data(self, op):
        for event_op, data in self.events:
            if event_op == op:
                return data
        return None


class FakeUser:
    def __init__(self, player_id, username, password):
        self.id = int(player_id)
        self.username = username
        self.password_hash = hash_password(password)
        self.ranking = 0
        self.last_login_at = None


class FakeSocket:
    """Dung thay Connection: `send` la dong bo va chi gom payload lai."""

    def __init__(self):
        self.messages = []

    def send(self, payload):
        self.messages.append(payload)


class MessageHandlerTest(unittest.TestCase):
    def setUp(self):
        self.player_manager = PlayerManager()
        self.room_manager = RoomManager()
        self.invite_manager = InviteManager(self.player_manager, self.room_manager)
        # users.id la BIGSERIAL; giao thuc JSON van tai chung duoi dang chuoi.
        self.alice_id = "1"
        self.bob_id = "2"
        self.alice_socket = object()
        self.bob_socket = object()
        self.write_queue = FakeQueue()

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
            write_queue=self.write_queue,
        )

    def _login_both(self, handler):
        handler.session.users = {"alice": FakeUser(self.alice_id, "alice", "test-password")}
        handler.handle({"type": "login", "username": "alice", "password": "test-password"}, self.alice_socket)
        handler.session.users = {"bob": FakeUser(self.bob_id, "bob", "test-password")}
        handler.handle({"type": "login", "username": "bob", "password": "test-password"}, self.bob_socket)

    def _start_game(self, handler):
        """Moi + chap nhan, tra ve room_id cua van vua mo."""
        invite_result = handler.handle(
            {"type": "invite", "inviteId": "alice-invites-bob", "toPlayerId": self.bob_id}, self.alice_socket
        )
        invite_id = invite_result[0]["payload"]["inviteId"]
        accepted = handler.handle({"type": "accept_invite", "inviteId": invite_id}, self.bob_socket)
        return accepted[0]["payload"]["room_id"]

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
        room_id = self._start_game(handler)

        result = handler.handle(
            {"type": "make_move", "room_id": room_id, "playerId": self.alice_id, "row": 0, "col": 0}, self.alice_socket
        )

        result_payloads = [delivery["payload"] for delivery in result if delivery["payload"]["type"] == "game_result"]
        self.assertEqual({"win", "lose"}, {payload["result"] for payload in result_payloads})
        self.assertEqual(RoomStatus.FINISHED, self.room_manager.get_room(room_id).status)
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.alice_id).status)
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.bob_id).status)

    def test_accepting_invite_creates_the_match_row_synchronously(self):
        handler = self._handler()
        self._login_both(handler)
        room_id = self._start_game(handler)

        matches = handler.session.added_of(Match)
        self.assertEqual(1, len(matches))
        match = matches[0]
        # room_id chinh la id database cap, ung dung khong tu sinh nua.
        self.assertEqual(room_id, str(match.id))
        self.assertEqual(int(self.alice_id), match.player_x_id)
        self.assertEqual(int(self.bob_id), match.player_o_id)
        self.assertEqual("playing", match.status)
        self.assertIsNotNone(match.started_at)
        # Va no khong con di qua hang doi ghi DB nua.
        self.assertEqual([], self.write_queue.ops())

    def test_match_row_failure_aborts_the_invite(self):
        handler = self._handler()
        self._login_both(handler)

        def no_flush():
            raise RuntimeError("database down")

        handler.session.flush = no_flush

        handler.handle(
            {"type": "invite", "inviteId": "alice-invites-bob", "toPlayerId": self.bob_id}, self.alice_socket
        )
        result = handler.handle({"type": "accept_invite", "inviteId": "alice-invites-bob"}, self.bob_socket)

        self.assertEqual("DATABASE_ERROR", result[0]["payload"]["code"])
        # Khong mo phong "mo coi" (khong co hang matches) de roi moi nuoc
        # di sau do deu vi pham khoa ngoai.
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.alice_id).status)
        self.assertEqual(PlayerStatus.IDLE, self.player_manager.get_player(self.bob_id).status)

    def test_moves_are_queued_in_order_before_the_result(self):
        handler = self._handler(board_factory=lambda: Caro(3, 3, winning_condition=3))
        self._login_both(handler)
        room_id = self._start_game(handler)

        # X thang hang 0; O chan o hang 1.
        script = [
            (self.alice_socket, self.alice_id, 0, 0),
            (self.bob_socket, self.bob_id, 1, 0),
            (self.alice_socket, self.alice_id, 0, 1),
            (self.bob_socket, self.bob_id, 1, 1),
            (self.alice_socket, self.alice_id, 0, 2),
        ]
        for sock, player_id, row, col in script:
            handler.handle(
                {"type": "make_move", "room_id": room_id, "playerId": player_id, "row": row, "col": col}, sock
            )

        moves = [data for op, data in self.write_queue.events if op == Op.INSERT_MOVE]
        self.assertEqual([1, 2, 3, 4, 5], [m["move_index"] for m in moves])
        self.assertEqual([(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)], [(m["row_idx"], m["col_idx"]) for m in moves])
        # So le la luot X, so chan la luot O.
        self.assertTrue(all(m["player_id"] == self.alice_id for m in moves if m["move_index"] % 2 == 1))
        self.assertTrue(all(m["player_id"] == self.bob_id for m in moves if m["move_index"] % 2 == 0))

        # Hang `matches` da ghi dong bo tu luc mo phong, nen hang doi chi
        # con cac nuoc di roi toi ket qua o cuoi.
        ops = self.write_queue.ops()
        self.assertEqual([Op.INSERT_MOVE] * 5 + [Op.UPDATE_MATCH_RESULT], ops)

        result = self.write_queue.first_data(Op.UPDATE_MATCH_RESULT)
        self.assertEqual("finished", result["status"])
        self.assertEqual("x_win", result["result"])
        self.assertEqual(self.alice_id, result["winner_id"])
        self.assertIsNotNone(result["ended_at"])

    def test_leaving_mid_game_queues_a_win_for_the_opponent(self):
        handler = self._handler(board_factory=lambda: Caro(3, 3, winning_condition=3))
        self._login_both(handler)
        room_id = self._start_game(handler)

        handler.handle({"type": "leave_room", "room_id": room_id}, self.alice_socket)

        result = self.write_queue.first_data(Op.UPDATE_MATCH_RESULT)
        self.assertEqual("finished", result["status"])
        self.assertEqual("o_win", result["result"])
        self.assertEqual(self.bob_id, result["winner_id"])

    def test_disconnect_mid_game_queues_a_win_for_the_opponent(self):
        handler = self._handler(board_factory=lambda: Caro(3, 3, winning_condition=3))
        self._login_both(handler)
        self._start_game(handler)

        handler.disconnect(self.bob_socket)

        result = self.write_queue.first_data(Op.UPDATE_MATCH_RESULT)
        self.assertEqual("finished", result["status"])
        self.assertEqual("x_win", result["result"])
        self.assertEqual(self.alice_id, result["winner_id"])

    def test_move_cannot_impersonate_another_player(self):
        handler = self._handler()
        self._login_both(handler)
        room = self.room_manager.create_room(self.alice_id, self.bob_id, "99")
        room.board_instance = Caro(3, 3, winning_condition=3)
        room.status = RoomStatus.PLAYING

        result = handler.handle(
            {"type": "make_move", "room_id": room.room_id, "playerId": self.alice_id, "row": 0, "col": 0},
            self.bob_socket,
        )

        self.assertEqual("FORBIDDEN", result[0]["payload"]["code"])
        self.assertEqual(".", room.board_instance.grid[0][0])
        # Nuoc di bi tu choi thi khong duoc ghi xuong database.
        self.assertNotIn(Op.INSERT_MOVE, self.write_queue.ops())

    def test_server_delivery_routes_origin_targeted_and_broadcast_messages(self):
        server = ServerHandler("127.0.0.1", 0)
        origin = FakeSocket()
        other = FakeSocket()
        server.connected_users.add_player(self.alice_id, "alice", origin)
        server.connected_users.add_player(self.bob_id, "bob", other)

        server._dispatch(
            [
                {"targets": [], "payload": {"type": "origin"}},
                {"targets": [self.bob_id], "payload": {"type": "targeted"}},
                {"targets": None, "payload": {"type": "broadcast"}},
            ],
            origin,
        )

        self.assertEqual([{"type": "origin"}, {"type": "broadcast"}], origin.messages)
        self.assertEqual([{"type": "targeted"}, {"type": "broadcast"}], other.messages)


if __name__ == "__main__":
    unittest.main()
