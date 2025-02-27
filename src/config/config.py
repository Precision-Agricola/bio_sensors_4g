"""Initialize the sensor registration and load the device and sensors configuation
"""
import json
from sensors.base import sensor_registry


RTC_CLK_PIN = 16  # Default CLK pin
RTC_DIO_PIN = 21  # Default DIO pin
RTC_CS_PIN = 23   # Default CS pin

def load_sensor_config(config_file='config/sensors.json'):
    """Loads sensor configurations from a JSON file and instantiates sensor objects.
        Args:
            config_file (str, optional): The path to the JSON configuration file.
                Defaults to 'config/sensors.json'.
        Returns:
            list: A list of instantiated sensor objects based on the configuration file.
                  Returns an empty list if there is an error loading the configuration
                  or if no valid sensors are found.
    """
    try:
        with open(config_file) as f:
            config = json.load(f)
        sensors = []
        for item in config:
            # Normalize model and protocol to uppercase
            model = item.get('model', '').strip().upper()
            protocol = item.get('protocol', '').strip().upper()
            key = (model, protocol)
            sensor_cls = sensor_registry.get(key)
            if sensor_cls:
                sensors.append(sensor_cls(**item))
            else:
                print(f"Skipping unknown sensor: {model} ({protocol})")
        print(f"Loaded Sensors {sensors}")
        return sensors
    except Exception as e:
        print(f"Error loading sensor config: {str(e)}")
        return []

def load_device_config(config_file='config/device_config.json'):
    """Loads device configuration from a JSON file.
        Args:
            config_file (str, optional): Path to the JSON configuration file.
                Defaults to 'config/device_config.json'.
        Returns:
            dict: A dictionary containing the device configuration.
                Returns a default configuration if the file cannot be loaded.
                The default configuration includes:
                - wifi: {'ssid': '', 'password': ''}
                - server_ip: '192.168.1.100'
                - port: 5000
        """

    try:
        with open(config_file) as f:
            return json.load(f)
    except:
        print('Error loading device config')
        return {
            'wifi': {'ssid': '', 'password': ''},
            'server_ip': '192.168.1.100',
            'port': 5000
        }
