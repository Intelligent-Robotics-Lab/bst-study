import socket
import time

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 7777))

print("Connected")

client.sendall(b'{"test":"hello"}\n')

print("Sent")

time.sleep(10)

client.close()

print("Closed")