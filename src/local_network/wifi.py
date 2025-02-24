"""Wifi Manager"""

import network
import urequests
from config import SSID, PASSWORD, SERVER_URL

if SSID is None:
    SSID = 'bio_sensors_access_point'
if PASSWORD is None:
    PASSWORD = '#ExitoAgricola1$'
if SERVER_URL is None:
    SERVER_URL = '192.168.1.100:8080'

def connect():
    """Connect to the WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print("WiFi connected")

def send_data(payload):
    """Send the payload to the Raspberry Pi server.

    Args:
        payload (str): JSON-encoded payload to send.
    """
    connect()
    try:
        response = urequests.post(SERVER_URL, data=payload)
        print("Data sent successfully:", response.text)
    except Exception as e:
        print("Error sending data:", e)
