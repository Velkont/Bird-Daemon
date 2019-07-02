import os
import socket
path="/var/run/bird/bird.ctl"
class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data=self.sock.recv(1024)
        print(data.decode("utf-8"))
    def showStatus(self):
        self.sock.send(b"show status\n")
        data=self.sock.recv(1024)
        print(data.decode("utf-8"))
    def showInterfaces(self):
        self.sock.send(b"show interfaces\n")
        data=self.sock.recv(1024)
        print(data.decode("utf-8"))
    def showNeighbors(self):
        self.sock.send(b"show ospf\n")
        data=self.sock.recv(1024)
        print(data.decode("utf-8"))
    def __del__(self):
        self.sock.close()
        
new_bird=Bird(path)
new_bird.showStatus()
new_bird.showInterfaces()
new_bird.showNeighbors()
del new_bird
 

    
