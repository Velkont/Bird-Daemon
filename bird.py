import socket
import time
import logging
import yaml
import os
import re
import asyncio
from jinja2 import Template

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)


class Config:
    def __init__(self):
        self.dir_name = os.path.dirname(__file__)
        self.config_file_name = os.path.join(self.dir_name, './config.yaml')

    def load_config(self):
        with open(self.config_file_name, "r") as config_file:
            config = yaml.load(config_file)
        return config

    def get_methods_config(self, instance_of_bird):
        config = self.load_config()
        methods = []
        dic_with_data_functions = {
            "Status": instance_of_bird.show_status,
            "Protocols": instance_of_bird.show_protocols,
            "Neighbors": instance_of_bird.show_neighbors,
            "Interfaces": instance_of_bird.show_interfaces
        }
        for method_params in config["methods"].values():
            if method_params["name"] == "Neighbors":
                data = dic_with_data_functions[method_params["name"]](
                    method_params["neighbor"])
                method_params.update({"data": data})
            else:
                data = dic_with_data_functions[method_params["name"]]()
                method_params.update({"data": data})
            methods.append(method_params)
        return methods

    def get_path(self, w):
        config = self.load_config()
        path = config["bird_paths"][w]
        return path

    def get_metrics_socket(self):
        config = self.load_config()
        host = config["metrics_socket"]["host"]
        port = config["metrics_socket"]["port"]
        return host, port


class Bird:
    def __init__(self, path):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path)
        data = self.sock.recv(2048).replace(b".", b"").split()
        if b"BIRD" not in data and b"ready" not in data:
            raise Exception("Socket is not correct")

    def validate_data(self, msg):
        if re.findall(r'10\d\d-?', msg) and re.findall(r'00\d\d-?', msg):
            return True
        else:
            return False

    def get_data(self, command):
        self.sock.send(("{0}{1}".format(command, "\n")).encode("utf-8"))
        data = self.sock.recv(1024)
        logging.debug(data)
        logging.debug("get_data end")
        data = data.decode("utf-8")
        while self.validate_data(data) is False:
            data += self.sock.recv(1024).decode("utf-8")
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
            if i.startswith('1000-'):
                dic.update({key: i.replace("1000-", "")})
            elif i.startswith('0013'):
                if i.find('Daemon is up and running') != -1:
                    dic.update({key: 1})
                else:
                    dic.update({key: 0})
            elif i.startswith('1011-'):
                ip = re.findall(r'\d+.\d+.\d+.\d+', i)[0]
                dic.update({key: ip})
            else:
                date = re.findall(r'\d+-\d+-\d+ \d+:\d+:\d+.\d+', i)[0]
                dic.update({key: date})
        data_to_return.append(dic)
        logging.debug("show_status end")
        logging.debug(data_to_return)
        logging.debug("--------------")
        return data_to_return

    def show_interfaces(self):
        data = self.get_data("show interfaces")
        data = data.split("\n")[:-2]
        logging.debug(data)
        data_to_return = []
        dic = {}
        keys = [x[5:] for x in data if x.find("index=") != -1]
        n = []
        j = -1
        for i in data:
            if i.find("index=") == -1:
                n.append(i[6:])
            if i.find("index=") != -1 or i == len(data) - 1:
                if j > -1:
                    dic.update({keys[j+1]: n})
                    n = []
                j += 1
        data_to_return.append(dic)
        logging.debug("show_interfaces end")
        logging.debug(data)
        logging.debug("--------------")
        return data_to_return

    def show_neighbors(self, name="", *args):
        data = self.get_data("show ospf neighbors {0}".format(name))
        if data.startswith("9001"):
            return None
        data = data.split('\n')[2:-2]
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
        logging.debug(data)
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
                if ID in dic.values() and param in dic:
                    metric = "{0}.{1}.{2} {3} {4}".format(
                        str(name), str(ID),
                        str(param), str(dic[param]),
                        str(int(time.time())))
                    data_to_return.append(metric)
                elif param in dic and ID is None:
                    metric = "{0}.{1} {2} {3}".format(
                        str(name), str(param),
                        str(dic[param]),
                        str(int(time.time())))
                    data_to_return.append(metric)
                elif ID in dic.values() and param is None:
                    for key in dic:
                        metric = "{0}.{1}.{2} {3} {4}".format(
                            str(name), str(ID),
                            str(key), str(dic[key]),
                            str(int(time.time())))
                        data_to_return.append(metric)
                elif "Version" in dic and param is None:
                    for key in dic:
                        metric = "{0}.{1} {2} {3}".format(
                            str(name), str(key),
                            str(dic[key]),
                            str(int(time.time())))
                        data_to_return.append(metric)

                elif ID is None and param is None:
                    key_ID = None
                    for key in dic:
                        if key_ID is None:
                            key_ID = key
                        metric = "{0}.{1}.{2} {3} {4}".format(
                            str(name), str(dic[key_ID]),
                            str(key), str(dic[key]),
                            str(int(time.time())))
                        data_to_return.append(metric)
            if not data_to_return:
                data_to_return.append("None")
            return data_to_return
        except Exception as error:
            logging.exception("error while converting table")
            logging.exception(error)
            logging.debug("--------------")

    @staticmethod
    def convert_from_bird_to_metrics(data, name, ID=None,
                                     param=None, **kwargs):
        if data is None:
            return ["None"]
        else:
            return FormatData.convert_bird_table(data, name, ID, param)


class Metrics:
    def __init__(self, metrics_socket):
        self.metrics_socket = metrics_socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect(self.metrics_socket)

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


class BirdConfig:
    def __init__(self, path_to_bird_config_test):
        self.dir_name = os.path.dirname(__file__)
        self.path_to_bird_config_test = os.path.join(
            self.dir_name,
            path_to_bird_config_test)
        self.path_to_template = os.path.join(self.dir_name, './template.txt')

    def render_bird_config(self, import_rules_External, export_rules_External,
                           ospf_area_External, import_rules_Internal,
                           export_rules_Internal, ospf_area_Internal,
                           **kwargs):
        with open(self.path_to_template) as template_file:
            text = template_file.read()
            template = Template(text)
            return template.render(import_rules_External=import_rules_External,
                                   export_rules_External=export_rules_External,
                                   ospf_area_External=ospf_area_External,
                                   import_rules_Internal=import_rules_Internal,
                                   export_rules_Internal=export_rules_Internal,
                                   ospf_area_Internal=ospf_area_Internal)

    def save_in_file(self, rendered_bird_config):
        with open(self.path_to_bird_config_test, "w+") as output_file:
            output_file.write(rendered_bird_config)


if __name__ == "__main__":
    new_config = Config()
    new_metrics = Metrics(new_config.get_metrics_socket())
    new_bird_config = BirdConfig(new_config.get_path("path_to_bird_config_test"))
    new_bird = Bird(new_config.get_path("path_to_bird"))
    new_bird_config.save_in_file(new_bird_config.render_bird_config(
        import_rules_External="all", export_rules_External="all",
        ospf_area_External="172.30.0.0", import_rules_Internal="all",
        export_rules_Internal="None", ospf_area_Internal="172.25.0.0"))
    loop = asyncio.get_event_loop()

    async def main_coroutine():
        while True:
            methods = new_config.get_methods_config(new_bird)
            for i in methods:
                data_to_send = FormatData.convert_from_bird_to_metrics(**i)
                new_metrics.send_metrics(data_to_send)
            await asyncio.sleep(20)
    try:
        asyncio.ensure_future(main_coroutine())
        loop.run_forever()
    finally:
        loop.close()
