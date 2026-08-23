from db import init_db
from network.server import ServerHandler
import asyncio


def run():
    init_db() 

if __name__ == "__main__":
    init_db()
