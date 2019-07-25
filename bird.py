import socket
import time
import logging
import yaml
import os
import re
import asyncio
from jinja2 import Template

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


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

    def get_path(self, target):
        config = self.load_config()
        path = config["bird_paths"][target]
        return path

    def get_metrics_socket(self):
        config = self.load_config()
        host = config["metrics_socket"]["host"]
        port = config["metrics_socket"]["port"]
        return host, port

    def get_announcement(self):
        config = self.load_config()
        announcement = {}
        for name, settings in config["announcement"].items():
            announcement.update({name: settings})
        return announcement

    def get_none_announcement(self):
        config = self.load_config()
        announcement = {}
        for name, settings in config["announcement"].items():
            announcement.update({name: settings})
        for i in announcement.values():
            i['import_rules'] = 'none'
            i['export_rules'] = 'none'
        return announcement

    def get_sleep_time(self, target):
        config = self.load_config()
        sleep_time = config['sleep_time'][target]
        return sleep_time


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
        elif re.findall(r'0002-?', msg) and re.findall(r'[08]0[02][02]', msg):
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

    def configure_check(self):
        data = self.get_data('configure check')
        logging.debug("configure_check_data")
        logging.debug(data)
        if data.find('0020') != -1:
            return True
        else:
            logging.debug(data)
            raise Exception('config is not correct')

    def configure(self):
        data = self.get_data('configure')
        logging.debug('configure data')
        logging.debug(data)
        logging.debug('----------------')

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
    def convert_state(table):
        try:
            if table[0]['State'] == 'Full/PtP':
                return True
            else:
                return False
        except IndexError as error:
            logging.exception('no data in show_neighbors')
            logging.exception(error)
            return False

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
    def __init__(self, path_to_bird_config):
        self.dir_name = os.path.dirname(__file__)
        self.path_to_bird_config = os.path.join(
            self.dir_name,
            path_to_bird_config)
        self.path_to_base_template = os.path.join(self.dir_name,
                                                  './base_template.txt')
        self.path_to_template = os.path.join(self.dir_name,
                                             './template.txt')

    def render_bird_config(self, announcement):
        with open(self.path_to_base_template) as base_template_file:
            with open(self.path_to_template) as template_file:
                base_text = base_template_file.read()
                template_text = template_file.read()
                template = Template(template_text)
                for neighbor_name, settings in announcement.items():
                    base_text = "{0}\n{1}\n".format(
                        base_text,
                        template.render(name=neighbor_name,
                                        import_rules=settings["import_rules"],
                                        export_rules=settings["export_rules"],
                                        area=settings["area"]))
        return base_text

    def save_in_file(self, rendered_bird_config):
        with open(self.path_to_bird_config, "w+") as output_file:
            output_file.write(rendered_bird_config)


class StateMachine:
    def __init__(self):
        self.state = True

    def is_up(self):
        return self.state

    def update(self, ls):
        if not all(ls) and self.is_up():
            self.change_state_to_off()
        if all(ls) and not self.is_up():
            self.change_state_to_on()

    def change_state_to_on(self):
        announcement = config.get_announcement()
        bird_config.save_in_file(
            bird_config.render_bird_config(announcement)
        )
        if bird.configure_check():
            bird.configure()
        else:
            raise Exception('Incorrect config')
        self.state = True

    def change_state_to_off(self):
        none_announcement = config.get_none_announcement()
        bird_config.save_in_file(
            bird_config.render_bird_config(none_announcement)
        )
        if bird.configure_check():
            bird.configure()
        else:
            raise Exception('Incorrect config')
        self.state = False


if __name__ == "__main__":
    config = Config()
    state_machine = StateMachine()
    metrics = Metrics(config.get_metrics_socket())
    bird_config = BirdConfig(config.get_path("path_to_bird_config"))
    bird = Bird(config.get_path("path_to_bird"))

    async def send_metrics_coroutine():
        while True:
            methods = config.get_methods_config(bird)
            for i in methods:
                data_to_send = FormatData.convert_from_bird_to_metrics(**i)
                metrics.send_metrics(data_to_send)
            await asyncio.sleep(config.get_sleep_time('metrics'))

    async def send_states_coroutine():
        while True:
            ospf_neighbors = config.get_announcement().keys()
            list_of_states = []
            for name in ospf_neighbors:
                list_of_states.append(
                    FormatData.convert_state(bird.show_neighbors(name))
                )
            state_machine.update(list_of_states)
            logging.debug('list_of_states')
            logging.debug(list_of_states)
            logging.debug('State')
            logging.debug(state_machine.state)
            logging.debug('---------------')
            await asyncio.sleep(config.get_sleep_time('states'))

    try:
        loop = asyncio.get_event_loop()
        tasks = [
            asyncio.ensure_future(send_metrics_coroutine()),
            asyncio.ensure_future(send_states_coroutine()),
        ]
        loop.run_until_complete(asyncio.wait(tasks))

    finally:
        loop.close()
