"""Frame protocol: 4-byte big-endian length header + UTF-8 JSON body.

Wire format of a single frame::

    ┌──────────────┬─────────────────────┐
    │ 4 bytes (>I) │  N bytes JSON/UTF-8 │
    │   N = len    │     payload         │
    └──────────────┴─────────────────────┘

This module is **socket-agnostic** — it only converts between
``dict`` ↔ ``bytes`` so it can be reused by both client and server.
"""

from __future__ import annotations

import json
import struct

MESSAGE_HEADER_SIZE: int = 4  # bytes — unsigned 32-bit big-endian


def encode_frame(payload: dict) -> bytes:
    """Serialize *payload* into a length-prefixed frame.

    Returns
    -------
    bytes
        ``header (4 B) + json_body``
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = struct.pack(">I", len(body))
    return header + body


def decode_frames(buffer: bytearray) -> tuple[list[dict], bytearray]:
    """Extract all complete frames from *buffer*.

    Parameters
    ----------
    buffer : bytearray
        Accumulated raw bytes (modified in-place is fine, but we return
        the unconsumed remainder for clarity).

    Returns
    -------
    tuple[list[dict], bytearray]
        ``(parsed_messages, remaining_buffer)``
    """
    messages: list[dict] = []
    offset = 0

    while offset + MESSAGE_HEADER_SIZE <= len(buffer):
        body_len = struct.unpack(
            ">I", buffer[offset : offset + MESSAGE_HEADER_SIZE]
        )[0]
        frame_end = offset + MESSAGE_HEADER_SIZE + body_len

        if frame_end > len(buffer):
            break  # incomplete frame — wait for more data

        raw_body = bytes(buffer[offset + MESSAGE_HEADER_SIZE : frame_end])
        offset = frame_end

        try:
            messages.append(json.loads(raw_body.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError):
            messages.append(None)  # type: ignore[arg-type]

    # Return unconsumed remainder
    return messages, bytearray(buffer[offset:])
