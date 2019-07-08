import socket
sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect(("",2003))
while 1:
    data=sock.recv(1024)
    if data == b"quit":
        sock.close()
        break
    if data != b"":
        print("Data:",data.decode("utf-8"))
