import socket
class Listener():
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", 2003))
        self.sock.listen(1)
        self.connection, self.address = self.sock.accept()
    def __del__(self):
        self.connection.close()
if __name__ == "__main__":
    new_listener = Listener()
    while 1:
        data = new_listener.connection.recv(1024)
        if data != b"":
	        print(data)

