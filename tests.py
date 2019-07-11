import unittest
import bird
import time
class TestBird(bird.Bird):
    def __init__(self):
        pass
    def getData(self, name):
        return self.data
    def __del__(self):
        pass
        
class TestBirdClass(unittest.TestCase):  
    def setUp(self):
        self.test_bird = TestBird()
    def testOutputShowStatus(self):
        self.test_bird.data = b'1013-Internal:\n Router ID   \tPri\t     State     \tDTime\tInterface  Router IP   \n 172.20.30.1\t  1\tFull/PtP  \t 31.317\tveth2internal 172.20.30.1    \n0000 \n'.decode("utf-8")
        endData = [{'Router ID': '172.20.30.1', 'Pri': '1', 'State': 'Full/PtP', 'DTime': '31.317', 'Interface': 'veth2internal', 'Router IP': '172.20.30.1'}]
        self.assertEqual(self.test_bird.showNeighbors("Internal"), endData)  
           
class TestFormatClass(unittest.TestCase):    
    def testOutputFromBirdToMetrics(self):
        startData = [{
            'Router ID': '172.20.30.1',
            'Pri': '1', 
            'State': 'Full/PtP', 
            'DTime': '37.453', 
            'Interface': 'veth2internal', 
            'Router IP': '172.20.30.1'
        }]
        endData = "Pri 1 " + str(int(time.time()))
        self.assertEqual(bird.FormatData.fromBirdToMetrics(startData, ID = '172.20.30.1', param = "Pri"), endData)
        
    def testOutputConvertBirdTable(self):
        startData = [{
            'Router ID': '172.20.30.1', 
            'Pri': '1', 
            'State': 'Full/PtP', 
            'DTime': '38.953', 
            'Interface': 'veth2internal', 
            'Router IP': '172.20.30.1'
        }]
        endData = "Pri 1 " + str(int(time.time()))
        self.assertEqual(bird.FormatData.convertBirdTable(startData, ID = '172.20.30.1', param = "Pri"), endData)
    def testOutputConvertBirdDic(self):
        startData = {
            'Version': 'BIRD 2.0.0', 
            'Router ID': '172.20.20.2', 
            'Current server time': '2019-07-11 14:54:14.324', 
            'Last reboot': '2019-07-11 10:38:11.166', 
            'Last reconfiguration': '2019-07-11 10:38:11.166', 
            'Status': 'Daemon is up and running'
        }
        endData = "Status Daemon is up and running " + str(int(time.time()))
        self.assertEqual(bird.FormatData.convertBirdDic(startData, param = "Status"), endData)
        
if __name__ == "__main__":
    unittest.main()
