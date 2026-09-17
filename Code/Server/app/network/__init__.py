"""app.network — TCP networking layer for the Caro game server.

Submodules
----------
- ``protocol``   — Frame encoding / decoding (no side-effects).
- ``connection`` — Per-client socket wrapper.
- ``server``     — Selector-driven event loop & message dispatch.
"""

from app.network.protocol import MESSAGE_HEADER_SIZE, decode_frames, encode_frame
from app.network.connection import Connection

__all__ = [
    "MESSAGE_HEADER_SIZE",
    "decode_frames",
    "encode_frame",
    "Connection",
]


def __getattr__(name: str):
    """Lazy-import ServerHandler to avoid pulling in DB / handler deps at
    import time (they require a running database connection)."""
    if name == "ServerHandler":
        from app.network.server import ServerHandler
        return ServerHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
