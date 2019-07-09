import os
import socket
import time
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
            for index_j, j in enumerate(i):
            	dataToReturn[index_i].update({keys[index_j]: i[index_j]})
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
        	if i.find("BIRD") != -1:
        		dataToReturn.update({keys[index]: i[5:]})
        	if i.find(" is ") != -1:
        		dataToReturn.update({keys[index]: i.split(" is ")[1]})
        	if i.find(" on ") != -1:
        		dataToReturn.update({keys[index]: i.split(" on ")[1]})
        	if i.find("Daemon") != -1:
        		dataToReturn.update({keys[index]: i[5:]})
        return dataToReturn   	
        
    def showInterfaces(self):
        self.sock.send(b"show interfaces\n")
        data = self.sock.recv(1024).decode("utf-8").split("\n")[:-2]
        dataToReturn = {}
        keys = [x[5:] for x in data if x.find("index=") != -1]
        n = []
        j = -1
        for index, i in enumerate(data):
        	if i.find("index=") == -1:
        		n.append(i[6:])
        	if i.find("index=") != -1 or i == len(data) - 1:
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
        
class Metrics:
	def __init__(self, path):
		self.path = path
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(("", 2003))
		self.sock.listen(1)
		self.connection, self.address = self.sock.accept()
		
	def convertTable(self, table, ID , param):
	    if table == None:
	        return "None"
	    for dic in table:
	        if ID == dic[list(dic.keys())[0]] and param in dic.keys():
	             return str(param) + " " + str(dic[param]) + " " + str(time.time())
	        else:
	            raise Exception("no such name or parameter")
	    
	def convertDic(self, dic, param):
	    if param in dic.keys():
	        return str(param) + " " + str(dic[param]) + " " + str(time.time())
	    else:
	        raise Exception("no such parameter")

	def createMetrics(self, name, info, ID, param):
		new_bird = Bird(self.path)
		d = {
		"Status": new_bird.showStatus,
		"Interfaces": new_bird.showInterfaces,
		"Neighbors": new_bird.showNeighbors,
		"Protocols": new_bird.showProtocols
		}
		if name == "Neighbors" or name == "Protocols":
		    return self.convertTable(d[name](info), ID, param)
		else:
		    return self.convertDic(d[name](), param)

	def sendMetrics(self, name, info = "", ID = None, param = "", **kwargs):
	    metrics = self.createMetrics(name, info, ID, param)
	    self.connection.send(metrics.encode("utf-8") + b"\n")

	def __del__(self):
		self.connection.close()
		
new_metrics = Metrics(path)
new_metrics.sendMetrics("Neighbors", info = "External", ID = "172.20.20.1", param = "State")
    
