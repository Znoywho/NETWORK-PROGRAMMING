import threading
from typing import Optional

from app.matchmaking.models import Player, PlayerStatus


class PlayerManager:
    def __init__(self):
        self._players: dict[str, Player] = {}
        self._lock = threading.Lock()

    def add_player(self, player_id: str, connection) -> Player:
        with self._lock:
            player = Player(player_id=player_id, connection=connection)
            self._players[player_id] = player
            return player

    def remove_player(self, player_id: str) -> None:
        with self._lock:
            self._players.pop(player_id, None)

    def get_player(self, player_id: str) -> Optional[Player]:
        with self._lock:
            return self._players.get(player_id)

    def set_status(self, player_id: str, status: PlayerStatus) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return False
            player.status = status
            return True

    def set_current_room(self, player_id: str, room_id: Optional[str]) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return False
            player.current_room_id = room_id
            return True

    def list_online(self) -> list[dict]:
        with self._lock:
            return [
                {"player_id": p.player_id, "status": p.status.value}
                for p in self._players.values()
            ]

    def is_online(self, player_id: str) -> bool:
        with self._lock:
            return player_id in self._players