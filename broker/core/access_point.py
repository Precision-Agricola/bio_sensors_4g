import network
import uasyncio as asyncio
import time
from config.secrets import WIFI_CONFIG

class AccessPointManager:
    def __init__(self, ssid=None, password=None):
        self.ssid = ssid or WIFI_CONFIG.get("ssid", "PrecisionAgricola")
        self.password = password or WIFI_CONFIG.get("password", "ag2025pass")
        self.ap = None

    async def setup_access_point(self):
        self.ap = network.WLAN(network.AP_IF)
        self.ap.config(essid=self.ssid, password=self.password)
        self.ap.active(True)
        timeout = 10  # seconds
        start = time.ticks_ms()
        while not self.ap.active():
            if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
                raise RuntimeError("AP activation timeout")
            await asyncio.sleep(0.1)
        print("AP Active:", self.ssid, "| IP:", self.ap.ifconfig()[0])
        return self.ap
