import os
import socket
path="/var/run/bird/bird.ctl"
class Bird:
    def __init__(self, path):
        self.path = path
    def showStatus(self):
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        sock.connect(self.path)
        sock.send("birdc".encode('utf-8'))
        sock.send("show status".encode('utf-8'))
        print("ОТПРАВЛЕНО")
        data=sock.recv(1024)
        print(data)
        sock.close()
    def showInterfaces(self):
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        sock.connect(self.path)
        sock.send("show interfaces".encode('utf-8'))
        print("ОТПРАВЛЕНО")
        data=sock.recv(1024)
        print(data)
        sock.close()
    def showNeighbors(self):
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        sock.connect(self.path)
        sock.send("show ospf neighbors".encode('utf-8'))
        print("ОТПРАВЛЕНО")
        data=sock.recv(1024)
        print(data)
        sock.close()
        
new_bird=Bird(path)
new_bird.showStatus()
new_bird.showInterfaces()
new_bird.showNeighbors()
 

    
