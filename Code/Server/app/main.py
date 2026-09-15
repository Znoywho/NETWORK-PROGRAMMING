from app.network.server import ServerHandler

if __name__ == "__main__":
    server = ServerHandler("0.0.0.0", 8765)
    print("======== Running Server ========")
    server.run()
