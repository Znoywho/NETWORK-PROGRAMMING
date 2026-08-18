import threading
import uuid
from typing import Optional

from app.models.matchmaking_models import Room

class RoomManager:
    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._lock = threading.Lock()

    def create_room(self, player_x_id: str, player_o_id: str) -> Room:
        with self._lock:
            room_id = str(uuid.uuid4())[:8]
            room = Room(room_id=room_id, player_x=player_x_id, player_o=player_o_id)
            self._rooms[room_id] = room
            return room

    def get_room(self, room_id: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_id)

    def remove_room(self, room_id: str) -> None:
        with self._lock:
            self._rooms.pop(room_id, None)

    def add_spectator(self, room_id: str, player_id: str) -> bool:
        with self._lock:
            room = self._rooms.get(room_id)
            if room:
                room.spectators.add(player_id)
                return True
            return False

    def remove_spectator(self, room_id: str, player_id: str) -> None:
        with self._lock:
            room = self._rooms.get(room_id)
            if room:
                room.spectators.discard(player_id)