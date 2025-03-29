import network
import time
from config.secrets import WIFI_CONFIG

class AccessPointManager:
    def __init__(self, ssid=None, password=None):
        self.ssid = ssid or WIFI_CONFIG.get("ssid", "PrecisionAgricola")
        self.password = password or WIFI_CONFIG.get("password", "ag2025pass")
        self.ap = None

    def setup_access_point(self):
        self.ap = network.WLAN(network.AP_IF)
        self.ap.config(essid=self.ssid, password=self.password)
        self.ap.active(True)
        start_time = time.time()
        timeout = 10
        while not self.ap.active():
            if time.time() - start_time > timeout:
                raise RuntimeError("Failed to activate access point")
            time.sleep(0.1)
        print("AP Active:", self.ssid, "| IP:", self.ap.ifconfig()[0])
        return self.ap
