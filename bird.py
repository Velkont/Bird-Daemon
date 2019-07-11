import os
import socket
import time
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
path = "/var/lib/docker-extvols/balancer-bird/run/bird.ctl"

class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data = self.sock.recv(1024).replace(b".", b"").split()
        if b"BIRD" not in data and b"ready" not in data:
        	raise Exception("Socket is not correct")
        	
    def getData(self, command):
        self.sock.send(command.encode("utf-8") + b"\n")
        data = self.sock.recv(1024)
        logging.debug("%s:%s", "getData end", data)
        data = data.decode("utf-8")
        return data
        
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
        logging.debug("%s:%s", "parseTable end", dataToReturn)
        return dataToReturn

    def showStatus(self):
        data = self.getData("show status")
        data = data.split("\n")
        keys = [
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
        logging.debug("%s:%s","showStatus end", dataToReturn)
        return dataToReturn   	
        
    def showInterfaces(self):
        data = self.getData("show interfaces")
        data=data.split("\n")[:-2]
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
        logging.debug("%s:%s", "showStatus end", dataToReturn)
        return dataToReturn
                
    def showNeighbors(self, name = "", *args):
        data = self.getData("show ospf neighbors %s" % name)
        if data[:4] == "9001":
            return None
        data = data.split("\n")[2:-2]
        keys = ["Router ID", "Pri", "State", "DTime", "Interface", "Router IP"]
        dataToReturn = self.parseTable(data, keys)
        logging.debug("%s:%s","showNeighbors end", dataToReturn)
        return dataToReturn
                        
    def showProtocols(self):
        data = self.getData("show protocols")
        data = data.split("\n")
        data = data[1:-2]
        data[0] = data[0][5:]
        keys = ["Name", "Proto", "Table", "State", "Since", "Info"]
        dataToReturn = self.parseTable(data, keys)
        logging.debug("%s:%s","showProtocols end", dataToReturn)
        return dataToReturn
             
    def __del__(self):
        self.sock.close()
        
class FormatData:
    @staticmethod
    def convertBirdTable(table, ID , param):
	    if table == None:
	        return "None"
	    for dic in table:
	        if ID == dic[list(dic.keys())[0]] and param in dic.keys():
	            dataToReturn = str(param) + " " + str(dic[param]) + " " + str(int(time.time()))
	            logging.debug("%s:%s","convertBirdTable end", dataToReturn)
	            return dataToReturn
	        else:
	            logging.error("no such name or parameter in Table")
    @staticmethod                       
    def convertBirdDic(dic, param):
	    if param in dic.keys():
	        dataToReturn = str(param) + " " + str(dic[param]) + " " + str(int(time.time()))
	        logging.debug("%s:%s","convertBirdDic end", dataToReturn)
	        return dataToReturn
	    else:
	        logging.error("no such name or parameter in Dictionary") 
    @staticmethod          
    def fromBirdToMetrics(data, ID = None, param = "", **kwargs):
	    if ID != None:
	        logging.debug("%s:%s","fromBirdToMetrics endTable", FormatData.convertBirdTable(data, ID, param))
	        return FormatData.convertBirdTable(data, ID, param)
	    else:
		    logging.debug("%s:%s","fromBirdToMetrics endTable", FormatData.convertBirdDic(data, param))
		    return FormatData.convertBirdDic(data, param)

class Metrics:
	def __init__(self):
	    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    self.sock.connect(("", 2003))

	def sendMetrics(self, data):
	    try:
	        self.sock.send(data.encode("utf-8"))
	        logging.info("Metrics sumbit completed")
	    except Exception:
	        logging.exception("Sending error")

	def __del__(self):
	    self.sock.close()

		
if __name__ == "__main__":
    new_metrics = Metrics()
    new_bird = Bird(path)
    while 1:
        dataToSend = FormatData.fromBirdToMetrics(data = new_bird.showNeighbors("Internal"), ID = "172.20.30.1", param="Pri")
        new_metrics.sendMetrics(dataToSend)
        new_metrics.sendMetrics(FormatData.fromBirdToMetrics(data = new_bird.showStatus(), param = "Status"))
        time.sleep(20)
        
