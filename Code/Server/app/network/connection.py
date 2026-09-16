"""Per-client connection: socket I/O, buffering, and selector management.

Delegates framing (encode / decode) to :mod:`app.network.protocol`.
"""

from __future__ import annotations

import logging
import selectors
import socket

from app.network.protocol import decode_frames, encode_frame

logger = logging.getLogger(__name__)


class Connection:
    def __init__(
        self,
        sock: socket.socket,
        addr: tuple,
        sel: selectors.BaseSelector,
    ):
        self.sock = sock
        self.addr = addr
        self.sel = sel
        self._recv_buff = bytearray()
        self._send_buff = bytearray()
        self.closed: bool = False
        self.player_id: str | None = None


    def recv(self):
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            return []

        if not data:
            raise RuntimeError("Peer closed.")

        self._recv_buff.extend(data)
        messages, self._recv_buff = decode_frames(self._recv_buff)
        return messages

    def send(self, payload: dict):
        if self.closed:
            return
        frame = encode_frame(payload)
        was_empty = len(self._send_buff) == 0
        self._send_buff.extend(frame)
        if was_empty:
            self._update_selector()

    def flush(self):
        if not self._send_buff:
            return
        try:
            sent = self.sock.send(self._send_buff)
            self._send_buff = self._send_buff[sent:]
        except BlockingIOError:
            pass
        except (ConnectionError, OSError):
            self.close()
            return

        self._update_selector()

    def close(self):
        if self.closed:
            return
        self.closed = True
        logger.info("Closing connection to %s", self.addr)

        try:
            self.sel.unregister(self.sock)
        except (KeyError, ValueError):
            pass

        try:
            self.sock.close()
        except OSError:
            pass

    def _update_selector(self):
        events = selectors.EVENT_READ
        if self._send_buff:
            events |= selectors.EVENT_WRITE
        try:
            self.sel.modify(self.sock, events, data=self)
        except (KeyError, ValueError):
            pass
