import os
import socket
path="/var/run/bird/bird.ctl"
class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data=self.sock.recv(1024).replace(b".",b"").split()
        if b"BIRD" not in data and b"ready" not in data:
                print("Something went wrong")
        if b"BIRD" in data and b"ready" in data:
                print("OK")
    def showStatus(self):
        self.sock.send(b"show status\n")
        data=self.sock.recv(1024).decode("utf-8").split("\n")
        keys=["Version","Router ID","Current server time","Last reboot","Last reconfiguration","Status"]
        dataToReturn={}
        for i in range(len(data)):
        	if data[i].find("BIRD")!=-1:
        		dataToReturn.update({keys[i]:data[i]})
        	if data[i].find(" is ")!=-1:
        		dataToReturn.update({keys[i]:data[i].split(" is ")[1]})
        	if data[i].find(" on ")!=-1:
        		dataToReturn.update({keys[i]:data[i].split(" on ")[1]})
        	if data[i].find("Daemon")!=-1:
        		dataToReturn.update({keys[i]:data[i][5:]})

        return dataToReturn
        	
        
    def showInterfaces(self):
        self.sock.send(b"show interfaces\n")
        data=self.sock.recv(1024).decode("utf-8").split("\n")
        del data[len(data)-1],data[len(data)-1]
        dataToReturn={}
        keys=[x[5:] for x in data if x.find("index=")!=-1]
        n=[]
        j=-1
        for i in range(len(data)):
        	if data[i].find("index=")==-1:
        		n.append(data[i][6:])
        	if data[i].find("index=")!=-1 or i==len(data)-1:
        		if j>-1:
        			dataToReturn.update({keys[j]:n})
        			n=[]
        		j+=1
        return dataToReturn
                
    def showNeighbors(self,*name):
        if len(name)>0:
                self.sock.send(b"show ospf "+ name[0].encode("utf-8") +b"\n")
                data=self.sock.recv(1024).decode("utf-8")
                if data[10:-1]=="Not a protocol":
                        return None
                else:
                        data=data.split("\n")
                        """Вообще не уверен, что этот блок хоть как-то работает, т.к. потестить на на чем, поэтому сделал по подобию с методом showProtocols, который у меня работает."""
                        del data[0],data[1]
                        k=[]
                        for i in data:
                                k.append(i.split())
                        keys=["Router ID","Pri","State","DTime","Interface","Router IP"]
                        dataToReturn=[]
                        for i in range(len(k)):
                                dataToReturn.append({})
                                n=0
                                for j in range(len(k[i])):
                                        dataToReturn[i].update({keys[n]:k[i][j]})
                                        n+=1
                        return dataToReturn

        else:
                self.sock.send(b"show ospf\n")
                data=self.sock.recv(1024).decode("utf-8")
                data=data[5:]
                if data=="There are multiple protocols running\n" or data=="There is no OSPF protocol running\n":
                        return None
  

                        
    def showProtocols(self):
        self.sock.send(b"show protocols\n")
        data=self.sock.recv(1024).decode("utf-8").split("\n")
        del data[0],data[len(data)-1],data[len(data)-1]
        k=[]
        for i in data:
                k.append(i.split())
        keys=["Name","Proto","Table","State","Since","Info"]
        dataToReturn=[]
        for i in range(len(k)):
                dataToReturn.append({})
                n=0
                for j in range(len(k[i])):
                        dataToReturn[i].update({keys[n]:k[i][j]})
                        n+=1
        return dataToReturn

             
    def __del__(self):
        self.sock.close()
        
new_bird=Bird(path)
new_bird.showStatus()
new_bird.showInterfaces()
new_bird.showNeighbors()
new_bird.showProtocols()
del new_bird
 

    
