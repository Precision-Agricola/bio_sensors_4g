"""Wifi Manager"""

import network
import urequests
from config.secrets import WIFI_CONFIG, SERVER_CONFIG

def connect():
    """Connect to the WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_CONFIG["ssid"], WIFI_CONFIG["password"])
        while not wlan.isconnected():
            pass
    print("WiFi connected")

def send_data(payload):
    """Send the payload to the Raspberry Pi server."""
    connect()
    try:
        response = urequests.post(SERVER_CONFIG["url"], data=payload)
        print("Data sent successfully:", response.text)
    except Exception as e:
        print("Error sending data:", e)
