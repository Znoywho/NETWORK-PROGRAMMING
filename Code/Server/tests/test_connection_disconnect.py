"""Regression test for TCP resets during a live client disconnect."""

import selectors

from app.network.connection import Connection


class ResetSocket:
    def recv(self, _size):
        raise ConnectionResetError("Connection reset by peer")


def test_tcp_reset_becomes_disconnect_signal():
    """A reset must reach ServerHandler's disconnect branch, not kill its loop."""
    selector = selectors.DefaultSelector()
    connection = Connection(ResetSocket(), ("127.0.0.1", 9999), selector)

    try:
        connection.recv()
    except RuntimeError as exc:
        assert "Peer connection lost" in str(exc)
        print("[OK] TCP reset duoc doi thanh disconnect signal")
    else:
        raise AssertionError("ConnectionResetError phai duoc doi thanh RuntimeError")
    finally:
        selector.close()


if __name__ == "__main__":
    test_tcp_reset_becomes_disconnect_signal()
