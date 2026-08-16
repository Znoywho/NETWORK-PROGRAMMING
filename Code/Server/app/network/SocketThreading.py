import socket
import sys
import threading


class SocketThreading:
    def __init__(self, SerIP, port):
        self.SerIP = SerIP
        self.port = port
        self.name = ""
        ##self.client = {}

    def serverAction(self):
        self.name = "Server"

        HOST = socket.gethostbyname(socket.gethostname())
        PORT = 3000

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(3)
        t1 = threading.Thread(target=self.server, args=(s,))
        t1.start()

    def server(self, s):
        self.conn, addr = s.accept()
        while True:
            print("Connected at ", addr)
            data = self.conn.recv(1024).decode()
            print(f"Data received from `{self.name}`: {data}")

    def clientAction(self, inputIP):
        self.name = "Client"

        HOST = inputIP
        PORT = 3000

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((HOST, PORT))

        t1 = threading.Thread(target=self.client)
        t1.start()

    def client(self):
        print("Data already sent")
        while True:
            data = self.conn.recv(1024).decode()
            print(f"Data from {self.name}: {data}")

    def sendData(self, text):
        text = text.encode("utf-8")
        self.conn.send(text)


if __name__ == "__main__":
    print("Start Socket.....")
    server = SocketThreading("hiii", 3000)
    server.serverAction()

    client = SocketThreading("hiii", 3000)
    client.clientAction(socket.gethostbyname(socket.gethostname()))

    client.sendData("Hello server")
