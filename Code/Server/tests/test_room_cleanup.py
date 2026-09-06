from app.matchmaking.room_manager import RoomManager
from app.models.matchmaking_models import RoomStatus


def test_cleanup_when_finished_and_no_spectators():
    rm = RoomManager()
    room = rm.create_room("alice", "bob")

    assert rm.cleanup_if_done(room.room_id) is False
    assert rm.get_room(room.room_id) is not None

    room.status = RoomStatus.FINISHED

    rm.add_spectator(room.room_id, "watcher_1")
    assert rm.cleanup_if_done(room.room_id) is False

    rm.remove_spectator(room.room_id, "watcher_1")
    assert rm.cleanup_if_done(room.room_id) is True
    assert rm.get_room(room.room_id) is None

    print("PASS: room chỉ bị dọn dẹp khi vừa kết thúc vừa hết khán giả")


def test_cleanup_ignores_nonexistent_room():
    rm = RoomManager()
    result = rm.cleanup_if_done("fake_room_id")
    assert result is False
    print("PASS: cleanup_if_done không lỗi khi room không tồn tại")


def test_mark_player_left():
    rm = RoomManager()
    room = rm.create_room("alice", "bob")
    rm.mark_player_left(room.room_id, "alice")

    updated_room = rm.get_room(room.room_id)
    assert "alice" in updated_room.players_left
    print("PASS: mark_player_left ghi nhận đúng người đã rời")


if __name__ == "__main__":
    test_cleanup_when_finished_and_no_spectators()
    test_cleanup_ignores_nonexistent_room()
    test_mark_player_left()