"""Main sensor modular reading

Version 1.0
@authors: santosm@bitelemetric.com, caleb@precisionagricola.com, raul@bitelemetric.com
"""

from machine import I2C, Pin
import time
import network
import json
from sensors.temperature.scd41 import SCD41

def connect_wifi(ssid, password):
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print('Network config:', wlan.ifconfig())
    return wlan

def main():

    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    sensors = {
        "scd41": SCD41(i2c),
    }

    for name, sensor in sensors.items():
        sensor.initialize()
    
    wifi = connect_wifi("rpi_ssid", "rpi_password")

    while True:
        readings = {}
        for name, sensor in sensors:
            readings[name] = sensor.get_reading()
        
        message = json.dumps(readings)
        print(f"Readings: {message}")

        time.sleep(30)

if __name__ == "__main__":
    main()
