"""Main sensor modular reading

Version 1.1
@authors: santosm@bitelemetric.com, caleb@precisionagricola.com, raul@bitelemetric.com
"""

import json
import time
from src.config.config import load_config
from src.network.wifi import Wifi
from src.network.messages import create_message

def load_device_config(config_file="src/config/device_config.json"):
    with open(config_file) as f:
        return json.load(f)

def main():
    # Load device and sensor configurations
    device_config = load_device_config()
    sensors = load_config("src/config/sensors.json") 

    # Extract WiFi and server details from device configuration
    wifi_conf = device_config.get("wifi", {})
    ssid = wifi_conf.get("ssid")
    password = wifi_conf.get("password")
    server_ip = device_config.get("server_ip", "192.168.1.100")
    port = device_config.get("port", 5000)

    # Connect to WiFi using the Wifi handler
    wifi = Wifi()
    if not wifi.connect(ssid, password):
        print("WiFi connection failed")
        return

    # Read sensors and collect their data
    sensor_data = {}
    for sensor in sensors:
        reading = sensor.read()
        sensor_data[sensor.name] = reading

    # Build and send the message
    message = create_message(sensor_data)
    if wifi.send(message, server_ip, port):
        print("Data sent successfully")
    else:
        print("Failed to send data")

if __name__ == "__main__":
    main()
