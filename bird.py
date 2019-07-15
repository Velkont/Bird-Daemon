import os
import socket
import time
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)
path = "/var/lib/docker-extvols/balancer-bird/run/bird.ctl"

class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data = self.sock.recv(1024).replace(b".", b"").split()
        if b"BIRD" not in data and b"ready" not in data:
        	raise Exception("Socket is not correct")
        	
    def get_data(self, command):
        self.sock.send(command.encode("utf-8") + b"\n")
        data = self.sock.recv(1024)
        logging.debug("get_data end")
        data = data.decode("utf-8")
        return data
        
    def parse_table(self, data, keys):
        k = []
        data_to_return = []
        for row in data:
            k.append(row.split())
        for row in k:
            dic = {}
            for n, key in zip(row, keys):
                dic.update({key: n})
            data_to_return.append(dic)
        logging.debug("parse_table end")
        logging.debug(data_to_return)
        logging.debug("--------------")
        return data_to_return
        

    def show_status(self):
        data = self.get_data("show status")
        logging.debug("show_status start")
        logging.debug(data)
        logging.debug("--------------")
        data = data.split("\n")
        keys = [
            "Version", "Router ID", "Current server time",
            "Last reboot", "Last reconfiguration", "Status"
        ]
        data_to_return = []
        dic = {}
        for i, key in zip(data, keys):
        	if i.find("BIRD") != -1:
        		dic.update({key: i[5:]})
        	if i.find(" is ") != -1:
        		dic.update({key: i.split(" is ")[1]})
        	if i.find(" on ") != -1:
        		dic.update({key: i.split(" on ")[1]})
        	if i.find("Daemon") != -1:
        	    if i.find("Daemon is up and running") != -1:
        	        dic.update({key: 1})
        	    else:
        	        dic.update({key: 0})
        data_to_return.append(dic)
        logging.debug("show_status end")
        logging.debug(data_to_return)
        logging.debug("--------------")
        return data_to_return   	
        
    def show_interfaces(self):
        data = self.get_data("show interfaces")
        data = data.split("\n")[:-2]
        data_to_return = []
        dic = {}
        keys = [x[5:] for x in data if x.find("index=") != -1]
        n = []
        j = -1
        for i, key in zip(data, keys):
        	if i.find("index=") == -1:
        		n.append(i[6:])
        	if i.find("index=") != -1 or i == len(data) - 1:
        		if j > -1:
        			data_to_return.update({key: n})
        			n = []
        		j += 1
        data_to_return.append(dic)
        logging.debug("show_status end")
        logging.debug("--------------")
        return data_to_return
                
    def show_neighbors(self, name="", *args):
        data = self.get_data("show ospf neighbors {0}".format(name))
        if data.startswith("9001"):
            return None
        data = data.split("\n")[2:-2]
        keys = ["Router ID", "Pri", "State", "DTime", "Interface", "Router IP"]
        data_to_return = self.parse_table(data, keys)
        logging.debug("show_neighbors end")
        logging.debug("--------------")
        return data_to_return
                        
    def show_protocols(self):
        data = self.get_data("show protocols")
        data = data.split("\n")
        data = data[1:-2]
        data[0] = data[0][5:]
        keys = ["Name", "Proto", "Table", "State", "Since", "Info"]
        data_to_return = self.parse_table(data, keys)
        logging.debug("show_protocols end")
        logging.debug("--------------")
        return data_to_return
             
    def __del__(self):
        self.sock.close()
        
class FormatData:
    @staticmethod
    def convert_bird_table(table, name, ID, param):
        data_to_return = []
        try:
            for dic in table:
                if param != None and ID == None: #единичная метрика в случае поиска по словарю
	                data_to_return.append("{0}.{1} {2} {3}".format(str(name), str(param), str(dic[param]), str(int(time.time()))))
                elif param != None and ID != None and ID in dic.values(): #единичная метрика в случае поиска по таблице
	                data_to_return.append("{0}.{1}.{2} {3} {4}".format(str(name), str(ID), str(param), str(dic[param]), str(int(time.time()))))
                elif param == None and ID in dic.values(): 
                    for key in dic: #продолжение накапливания метрик в случае выбора строки
	                    data_to_return.append("{0}.{1}.{2} {3} {4}".format(str(name), str(ID), str(key), str(dic[key]), str(int(time.time()))))

                elif param == None and "Version" in dic:
                     for key in dic: #продолжение накапливания метрик в случае выбора полного словаря
                        data_to_return.append("{0}.{1} {2} {3}".format(str(name), str(key), str(dic[key]), str(int(time.time()))))
                elif param == None and ID == None:
                    key_ID = None 
                    for key in dic: #продолжение накапливания метрик в случае выбора полной таблицы
                        if key_ID == None:
                            key_ID = key
                        data_to_return.append("{0}.{1}.{2} {3} {4}".format(str(name), str(dic[key_ID]), str(key), str(dic[key]), str(int(time.time()))))
            if data_to_return == []:
	            raise KeyError
            return data_to_return
        except AttributeError as error:
	        logging.exception(error)
	        logging.exception("no neighbor name put")
	        logging.debug("--------------")
        except KeyError as error:
	        logging.exception(error)
	        logging.exception("no such parameter or ID")
	        logging.debug("--------------")
        return data_to_return
	        
	            
    @staticmethod          
    def convert_from_bird_to_metrics(data, name, ID=None, param=None, **kwargs):
        if data == None:
	        return "None"
        else:
            return FormatData.convert_bird_table(data, name, ID, param)

class Metrics:
	def __init__(self):
	    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    self.sock.connect(("", 2003))

	def send_metrics(self, data):
	    logging.debug("sen_metrics start")
	    logging.debug(data)
	    logging.debug("--------------")
	    try:    
	        for i in data:
	            self.sock.send(i.encode("utf-8"))

	    except Exception as error:
	        logging.exception("Sending error")
	        logging.exception(error)
	        logging.debug("--------------")

	def __del__(self):
	    self.sock.close()

		
if __name__ == "__main__":
    new_metrics = Metrics()
    new_bird = Bird(path)
    config = [
        {"data": new_bird.show_status(), "name": "Status"},
        {"data": new_bird.show_protocols(), "name": "Protocols", "ID": "Internal"},
        {"data": new_bird.show_neighbors("Internal"), "name": "Neighbors"}
    ]
    while 1:
        for i in config:
            data_to_send = FormatData.convert_from_bird_to_metrics(**i)
            new_metrics.send_metrics(data_to_send)
        time.sleep(20)
        
