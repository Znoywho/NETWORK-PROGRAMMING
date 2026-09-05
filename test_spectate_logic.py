from matchmaking.player_manager import PlayerManager
from matchmaking.room_manager import RoomManager
from matchmaking.invite_manager import InviteManager
from handlers.matchmaking_handlers import MatchmakingHandlers
from models.matchmaking_models import PlayerStatus


# Khởi tạo managers
pm = PlayerManager()
rm = RoomManager()
im = InviteManager(pm, rm)
handlers = MatchmakingHandlers(pm, rm, im)

# Tạo player muốn xem
pm.add_player("spectator_test", "spectator_test", None)

# Tạo một room có 2 người chơi
room = rm.create_room("player_x", "player_o")

print("ROOM ID:", room.room_id)

# Gửi yêu cầu spectate
result = handlers.handle_spectate(
    "spectator_test",
    {
        "room_id": room.room_id
    }
)

print("SPECTATE RESULT:", result)

# Kiểm tra trạng thái
player = pm.get_player("spectator_test")
room = rm.get_room(room.room_id)

print("PLAYER STATUS:", player.status)
print("CURRENT ROOM:", player.current_room_id)
print("SPECTATORS:", room.spectators)

# Kiểm tra kết quả
assert result["success"] is True
assert player.status.value == "spectating"
assert player.current_room_id == room.room_id
assert "spectator_test" in room.spectators

print("\nSPECTATE TEST PASSED")