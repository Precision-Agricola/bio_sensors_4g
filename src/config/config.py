"""Initialize the sensor registration and load the device and sensors configuation
"""
import json
from sensors.base import sensor_registry

RTC_CLK_PIN = 16
RTC_DIO_PIN = 21
RTC_CS_PIN = 23
AERATOR_PIN_A = 12
AERATOR_PIN_B = 27
BOOT_SELECTOR_PIN = 25
TEST_SELECTOR_PIN = 26

# Estado del sistema (variables)
_runtime_state = {
    "CURRENT_MODE": "EMERGENCY",  # Valor por defecto
    "CURRENT_SPEED": 1            # Valor por defecto
}

# Getters y setters para un mejor control
def get_mode():
    return _runtime_state["CURRENT_MODE"]

def set_mode(mode):
    _runtime_state["CURRENT_MODE"] = mode

def get_speed():
    return _runtime_state["CURRENT_SPEED"]

def set_speed(speed):
    _runtime_state["CURRENT_SPEED"] = speed

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
