from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.matchmaking.invite_manager import InviteManager
from app.models.matchmaking_models import PlayerStatus
from app.game.caro import Caro


def make_board():
    return Caro(rows=15, cols=15, winning_condition=5, XO="X")


def setup():
    pm = PlayerManager()
    rm = RoomManager()
    im = InviteManager(pm, rm)
    pm.add_player("alice", username="alice", connection=None)
    pm.add_player("bob", username="bob", connection=None)
    return pm, rm, im


def test_send_invite_success():
    pm, rm, im = setup()
    result = im.send_invite("alice", "bob")
    assert result["success"] is True
    assert "invite_id" in result
    print("PASS: Gửi lời mời thành công khi cả 2 người chơi đều đang rảnh")


def test_accept_invite_creates_room_with_board():
    pm, rm, im = setup()
    invite = im.send_invite("alice", "bob")
    result = im.accept_invite(invite["invite_id"], board_factory=make_board, room_id="room_1")

    assert result["success"] is True
    assert result["player_x"] == "alice"
    assert result["player_o"] == "bob"

    room = rm.get_room(result["room_id"])
    assert room is not None
    assert isinstance(room.board_instance, Caro)
    assert room.board_instance.rows == 15

    assert pm.get_player("alice").status == PlayerStatus.PLAYING
    assert pm.get_player("bob").status == PlayerStatus.PLAYING
    print("PASS: Chấp nhận lời mời tạo phòng đúng")


def test_reject_invite():
    pm, rm, im = setup()
    invite = im.send_invite("alice", "bob")
    result = im.reject_invite(invite["invite_id"])
    assert result["success"] is True
    print("PASS: Từ chối lời mời hoạt động đúng")


if __name__ == "__main__":
    test_send_invite_success()
    test_accept_invite_creates_room_with_board()
    test_reject_invite()