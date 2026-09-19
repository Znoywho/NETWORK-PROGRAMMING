import time
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.matchmaking.invite_manager import InviteManager


def setup():
    pm = PlayerManager()
    rm = RoomManager()
    im = InviteManager(pm, rm)
    pm.add_player("alice", username="alice", connection=None)
    pm.add_player("bob", username="bob", connection=None)
    return pm, rm, im


def test_cannot_invite_self():
    pm, rm, im = setup()
    result = im.send_invite("alice", "alice")
    assert result["success"] is False
    assert result["reason"] == "cannot_invite_self"
    print("PASS: không thể tự mời chính mình")


def test_invite_not_expired_immediately():
    pm, rm, im = setup()
    invite = im.send_invite("alice", "bob")
    is_expired = im.is_invite_expired(invite["invite_id"], timeout_seconds=30)
    assert is_expired is False
    print("PASS: lời mời mới gửi chưa hết hạn")


def test_invite_expired_check_with_fake_old_timestamp():
    pm, rm, im = setup()
    invite = im.send_invite("alice", "bob")
    invite_id = invite["invite_id"]

    im._pending_invites[invite_id]["timestamp"] = time.time() - 100

    is_expired = im.is_invite_expired(invite_id, timeout_seconds=30)
    assert is_expired is True
    print("PASS: lời mời cũ hơn 30 giây được nhận diện là hết hạn")


if __name__ == "__main__":
    test_cannot_invite_self()
    test_invite_not_expired_immediately()
    test_invite_expired_check_with_fake_old_timestamp()