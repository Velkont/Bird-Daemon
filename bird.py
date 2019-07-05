import os
import socket
path = "/var/lib/docker-extvols/balancer-bird/run/bird.ctl"
class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data = self.sock.recv(1024).replace(b".", b"").split()
        if b"BIRD" not in data and b"ready" not in data:
        	raise Exception("Socket is not correct")

    def parseTable(self, data, keys):
        k = []
        dataToReturn = []
        for i in data:
        	k.append(i.split())
        for index_i, i in enumerate(k):
            dataToReturn.append({})
            n = 0
            for index_j, j in enumerate(k[index_i]):
            	dataToReturn[index_i].update({keys[index_j]: k[index_i][index_j]})
            	n += 1
        return dataToReturn

    def showStatus(self):
        self.sock.send(b"show status\n")
        data=self.sock.recv(1024).decode("utf-8").split("\n")
        keys=[
            "Version", "Router ID", "Current server time",
            "Last reboot", "Last reconfiguration", "Status"
            ]
        dataToReturn = {}
        for index, i in enumerate(data):
        	if data[index].find("BIRD") != -1:
        		dataToReturn.update({keys[index]: data[index][5:]})
        	if data[index].find(" is ") != -1:
        		dataToReturn.update({keys[index]: data[index].split(" is ")[1]})
        	if data[index].find(" on ") != -1:
        		dataToReturn.update({keys[index]: data[index].split(" on ")[1]})
        	if data[index].find("Daemon") != -1:
        		dataToReturn.update({keys[index]: data[index][5:]})
        return dataToReturn   	
        
    def showInterfaces(self):
        self.sock.send(b"show interfaces\n")
        data = self.sock.recv(1024).decode("utf-8").split("\n")[:-2]
        dataToReturn = {}
        keys = [x[5:] for x in data if x.find("index=") != -1]
        n = []
        j = -1
        for index, i in enumerate(data):
        	if data[index].find("index=") == -1:
        		n.append(data[index][6:])
        	if data[index].find("index=") != -1 or i == len(data) - 1:
        		if j > -1:
        			dataToReturn.update({keys[j]: n})
        			n = []
        		j += 1
        return dataToReturn
                
    def showNeighbors(self, name="", *args):
        self.sock.send(b"show ospf neighbors "
                       +name.encode("utf-8") 
                       +b"\n")
        data = self.sock.recv(1024).decode("utf-8")
        if data[:4] == "9001":
            return None
        data = data.split("\n")[2:-2]
        keys = ["Router ID", "Pri", "State", "DTime", "Interface", "Router IP"]
        dataToReturn = self.parseTable(data, keys)
        return dataToReturn
                        
    def showProtocols(self):
        self.sock.send(b"show protocols\n")
        data = self.sock.recv(1024).decode("utf-8").split("\n")
        data = data[1:-2]
        data[0] = data[0][5:]
        keys = ["Name", "Proto", "Table", "State", "Since", "Info"]
        dataToReturn = self.parseTable(data, keys)
        return dataToReturn

             
    def __del__(self):
        self.sock.close()
        
new_bird = Bird(path)
print(new_bird.showStatus())
print(new_bird.showInterfaces())
print(new_bird.showNeighbors("External"))
print(new_bird.showProtocols())
 

    
