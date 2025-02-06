import unittest
from src.network.wifi import Wifi

# Fake WLAN to simulate no connection.
class FakeWLAN:
    def __init__(self, mode):
        self.connected = False
    def active(self, state):
        pass
    def isconnected(self):
        return self.connected
    def connect(self, ssid, password):
        pass

# Fake Socket to force a send error.
class FakeSocket:
    def __init__(self, *args, **kwargs):
        pass
    def connect(self, addr):
        raise Exception("Forced socket error")
    def send(self, data):
        pass
    def close(self):
        pass

class TestWifi(unittest.TestCase):
    def setUp(self):
        # Override WLAN and socket.socket in the wifi module.
        import src.network.wifi as wifi_mod
        wifi_mod.network.WLAN = lambda mode: FakeWLAN(mode)
        wifi_mod.socket.socket = lambda *args, **kwargs: FakeSocket()
        self.wifi = Wifi()

    def test_connect_timeout(self):
        # With fake WLAN, connection never occurs.
        result = self.wifi.connect("dummy", "dummy", timeout=1)
        self.assertFalse(result)

    def test_send_failure(self):
        # Force WLAN to be connected.
        self.wifi.wlan.connected = True
        result = self.wifi.send({"test": "data"}, "127.0.0.1", 5000)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
