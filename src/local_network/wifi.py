"""Wifi Manager"""

import local_network
import time
import socket
import json

class Wifi:
    def __init__(self):
        self.wlan = local_network.WLAN(local_network.STA_IF)
        self.wlan.active(True)

    def connect(self, ssid, password, timeout=10):
        if self.wlan.isconnected():
            return True
        print("Connecting to WiFi...")
        self.wlan.connect(ssid, password)
        start = time.time()
        while not self.wlan.isconnected():
            if time.time() - start > timeout:
                print("WiFi connection timeout")
                return False
            time.sleep(1)
        print("Connected to WiFi")
        return True

    def send(self, data, server_ip, port):
        try:
            addr_info = socket.getaddrinfo(server_ip, port)[0][-1]
            s = socket.socket()
            s.connect(addr_info)
            s.send(json.dumps(data).encode())
            s.close()
            return True
        except Exception as e:
            print("Send error:", e)
            return False
