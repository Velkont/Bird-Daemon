import socket
sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 2003))
sock.listen(1)
connection, address = sock.accept()
try:
	while 1:
	    data=connection.recv(1024)
	    if data != b"":
	        print(data)
finally:
    connection.close()
