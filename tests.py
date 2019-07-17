import unittest
import bird
import time


class TestBird(bird.Bird):
    def __init__(self):
        pass

    def get_data(self, name):
        return self.data

    def __del__(self):
        pass


class TestBirdClass(unittest.TestCase):

    def setUp(self):
        self.test_bird = TestBird()

    def test_output_show_neighbors(self):
        self.test_bird.data = b'''1013-Internal:\n Router ID   \tPri\t State     \tDTime\tInterface  Router IP \n 172.20.30.1\t  1\tFull/PtP \t 31.317\tveth2internal 172.20.30.1 \n0000 \n'''.decode("utf-8")
        end_data = [{
            'Router ID': '172.20.30.1',
            'Pri': '1',
            'State': 'Full/PtP',
            'DTime': '31.317',
            'Interface': 'veth2internal',
            'Router IP': '172.20.30.1'
        }]
        self.assertEqual(self.test_bird.show_neighbors("Internal"), end_data)

    def test_output_show_neighbors_none(self):
        self.test_bird.data = '''9001 There are
                              multiple OSPF protocols running\n'''
        self.assertEqual(None, self.test_bird.show_neighbors())

    def test_parse_table(self):
        self.test_bird.data = [''' 172.20.30.1\t  1\tFull/PtP
                               \t 33.217\tveth2internal 172.20.30.1    ''']
        end_data = [{
            'Router ID': '172.20.30.1',
            'Pri': '1',
            'State': 'Full/PtP',
            'DTime': '33.217',
            'Interface': 'veth2internal',
            'Router IP': '172.20.30.1'
        }]
        keys = ["Router ID", "Pri", "State", "DTime", "Interface", "Router IP"]
        self.assertEqual(end_data,
                         self.test_bird.parse_table(self.test_bird.data, keys))

    def test_show_status(self):
        self.test_bird.data = """1000-BIRD 2.0.0
                                 1011-Router ID is 172.20.20.2
                                 Current server time is 2019-07-15 07:57:33.909
                                 Last reboot on 2019-07-15 05:42:51.595
                                 Last reconfiguration on 2019-07-15 05:42:51.595
                                 0013 Daemon is up and running"""
        end_data = [{
            'Version': 'BIRD 2.0.0',
            'Router ID': '172.20.20.2',
            'Current server time': '2019-07-15 07:57:33.909',
            'Last reboot': '2019-07-15 05:42:51.595',
            'Last reconfiguration': '2019-07-15 05:42:51.595',
            'Status': 1
        }]
        self.assertEqual(self.test_bird.show_status(), end_data)


class TestFormatClass(unittest.TestCase):
    def setUp(self):
        self.test_dic = [
            {'Name': 'direct1', 'Proto': 'Direct', 'Table': '---',
             'State': 'up', 'Since': '17:26:29.843'},
            {'Name': 'kernel1', 'Proto': 'Kernel', 'Table': 'master4',
             'State': 'up', 'Since': '17:26:29.843'},
            {'Name': 'device1', 'Proto': 'Device', 'Table': '---',
             'State': 'up', 'Since': '17:26:29.843'},
            {'Name': 'static1', 'Proto': 'Static', 'Table': 'master4',
             'State': 'up', 'Since': '17:26:29.843'},
            {'Name': 'External', 'Proto': 'OSPF', 'Table': 'master4',
             'State': 'up', 'Since': '17:26:29.843', 'Info': 'Running'},
            {'Name': 'Internal', 'Proto': 'OSPF', 'Table': 'master4',
             'State': 'up', 'Since': '17:26:29.843', 'Info': 'Running'}
        ]
        self.test_line = [{
            'Router ID': '172.20.30.1',
            'Pri': '1',
            'State': 'Full/PtP',
            'DTime': '37.453',
            'Interface': 'veth2internal',
            'Router IP': '172.20.30.1'
        }]

    def test_output_from_bird_to_metrics(self):
        start_data = self.test_line
        end_data = ["Neighbors.172.20.30.1.Pri 1 " + str(int(time.time()))]
        self.assertEqual(
            end_data,
            bird.FormatData.convert_from_bird_to_metrics(start_data,
                                                         name="Neighbors",
                                                         ID='172.20.30.1',
                                                         param="Pri"))

    def test_output_convert_bird_table_neighbors(self):
        start_data = self.test_line
        end_data = ["Neighbors.172.20.30.1.Pri 1 " + str(int(time.time()))]
        self.assertEqual(end_data,
                         bird.FormatData.convert_bird_table(start_data,
                                                            name="Neighbors",
                                                            ID='172.20.30.1',
                                                            param="Pri"))

    def test_output_convert_bird_table_protocols(self):
        start_data = self.test_dic
        data = [
            'Protocols.Internal.Name Internal',
            'Protocols.Internal.Proto OSPF',
            'Protocols.Internal.Table master4',
            'Protocols.Internal.State up',
        ]
        end_data = []
        for i in data:
            end_data.append('{0} {1}'.format(i, str(int(time.time()))))

        self.assertEqual(end_data,
                         bird.FormatData.convert_bird_table(start_data,
                                                            name="Protocols",
                                                            ID='Internal',
                                                            param=None)[0:4])


if __name__ == "__main__":
    unittest.main()
