import socket
import sys

HOST = socket.gethostbyname(socket.gethostname())
PORT = 3000

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
except socket.gaierror as err:
    print(err)


while True:
    data = input("Enter your message")
    data = data.encode("utf-8")
    s.send(data)
