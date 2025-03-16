"""Core Wifi"""

import network

def setup_access_point(ssid, password):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    while not ap.active:
        pass
    print(f"Access Point Activated\nSSID: {ssid}\nIP: {ap.ifconfig()[0]}")
    return ap
