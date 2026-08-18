from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time
from app.game.caro import Caro

class PlayerStatus(Enum):
    IDLE = "idle"          # đang rảnh
    PLAYING = "playing"    # đang đấu
    SPECTATING = "spectating"  # đang xem

class RoomStatus(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

@dataclass
class Player:
    player_id: str
    connection: object          # đối tượng socket/websocket do module 1 cung cấp
    status: PlayerStatus = PlayerStatus.IDLE
    current_room_id: Optional[str] = None
    connected_at: float = field(default_factory=time.time)

@dataclass
class Room:
    room_id: str
    player_x: str                # player_id của người đi X
    player_o: str                # player_id của người đi O
    status: RoomStatus = RoomStatus.WAITING
    board_instance: Optional[Caro] = None  # do module 2 (Game Logic) cấp
    spectators: set = field(default_factory=set)  # set player_id khán giả
    created_at: float = field(default_factory=time.time)

    def get_player_id_by_turn(self, turn: int) -> Optional[str]:
        if turn == 1:
            return self.player_x
        elif turn == 2:
            return self.player_o
        return None