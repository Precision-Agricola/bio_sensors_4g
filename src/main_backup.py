import sensors.amonia.sen0567 
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901

"""Main sensor modular reading

Version 1.1
@authors: santosm@bitelemetric.com, caleb@precisionagricola.com, raul@bitelemetric.com
"""


import time
from config.config import load_sensor_config, load_device_config
from local_network.wifi import Wifi
from local_network.messages import create_message

def main():
    device_config = load_device_config()
    sensors = load_sensor_config()
    print("Device config:", device_config)
    print("Sensors loaded:", sensors)

    # Setup WiFi
    wifi = Wifi()
    wifi_config = device_config.get('wifi', {})
    if not wifi.connect(wifi_config.get('ssid'), wifi_config.get('password')):
        print("WiFi connection failed")
        return
    else:
        print("WiFi connected")

    while True:
        try:
            sensor_data = {}
            for sensor in sensors:
                try:
                    reading = sensor.read()
                    sensor_data[sensor.name] = reading
                except Exception as e:
                    print(f"Error reading {sensor.name}: {str(e)}")
            if sensor_data:
                message = create_message(sensor_data)
                wifi.send(
                    message,
                    device_config.get('server_ip', '192.168.1.100'),
                    device_config.get('port', 5000)
                )
            time.sleep(5)
        except Exception as e:
            print(f"Main loop error: {str(e)}")
            time.sleep(5)

if __name__ == '__main__':
    main()

