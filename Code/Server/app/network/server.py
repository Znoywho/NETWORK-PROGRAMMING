import logging
import selectors
import socket

from app.handlers.message_handlers import MessageHandler
from app.matchmaking.invite_manager import InviteManager
from app.matchmaking.player_manager import PlayerManager
from app.matchmaking.room_manager import RoomManager
from app.network.connection import Connection

logger = logging.getLogger(__name__)

class ServerHandler:

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        self.connected_users = PlayerManager()
        self.rooms = RoomManager()
        self.invitation = InviteManager(self.connected_users, self.rooms)
        self.message_handler = MessageHandler(
            self.connected_users, self.rooms, self.invitation
        )

        self.sel = selectors.DefaultSelector()

    def create_new_match(self, player1, player2):
        # NOTE: random ID
        self.current_match = match(player1, player2, 100)
        print(f"Create new match!: ID {self.current_match.match_id}")

    def _accept(self, listener: socket.socket) -> None:
        conn, addr = listener.accept()
        conn.setblocking(Falhttps://github.com/Znoywho/NETWORK-PROGRAMMING/pull/25/conflict?name=Code%252FServer%252Fapp%252Fnetwork%252Fserver.py&ancestor_oid=49b30504f01d0970764c47e18e611c4ee0529e1e&base_oid=e7161e492df316f56fcd5ab08abe1bccee5d2d7e&head_oid=36dd0e72abaf5045020311c4da4a043bc3244995se)
        connection = Connection(conn, addr, self.sel)
        self.sel.register(conn, selectors.EVENT_READ, data=connection)
        logger.info("Client connected: %s", addr)

    def _handle_client(self, conn: Connection, mask: int) -> None:
        """Process selector events for an established connection."""
        if mask & selectors.EVENT_READ:
            try:
                messages = conn.recv()
            except RuntimeError:
                # Peer closed the connection
                self._handle_disconnect(conn)
                return

            for msg in messages:
                deliveries = self.message_handler.handle(msg, conn)
                self._dispatch(deliveries, conn)

        if mask & selectors.EVENT_WRITE:
            conn.flush()

    def _handle_disconnect(self, conn: Connection) -> None:
        """Clean up after a client disconnects."""
        logger.info("Client disconnected: %s", conn.addr)
        deliveries = self.message_handler.disconnect(conn)
        self._dispatch(deliveries, conn)
        conn.close()

    def _dispatch(self, deliveries: list[dict], sender: Connection) -> None:
        for delivery in deliveries:
            targets = delivery["targets"]
            payload = delivery["payload"]

            if targets is None:
                # Broadcast to every online player
                for info in self.connected_users.list_online():
                    player = self.connected_users.get_player(info["player_id"])
                    if player and player.connection:
                        player.connection.send(payload)

            elif len(targets) == 0:
                # Reply only to the socket that sent the request
                sender.send(payload)

            else:
                # Send to specific player IDs
                for player_id in targets:
                    player = self.connected_users.get_player(player_id)
                    if player and player.connection:
                        player.connection.send(payload)

    def run(self) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen()
        listener.setblocking(False)
        self.sel.register(listener, selectors.EVENT_READ, data=None)

        logger.info("Server running on %s:%s", self.host, self.port)
        print(f"Server is running HOST: {self.host} | PORT: {self.port}")

        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # Listener socket — accept new connection
                        self._accept(key.fileobj)
                    else:
                        # Client connection — read / write
                        self._handle_client(key.data, mask)
        except KeyboardInterrupt:
            print("\nServer shutting down.")
        finally:
            self.sel.close()
