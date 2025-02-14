import json
from sensors.base import sensor_registry

def load_sensor_config(config_file='config/sensors.json'):
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
        return sensors
    except Exception as e:
        print(f"Error loading sensor config: {str(e)}")
        return []

def load_device_config(config_file='config/device_config.json'):
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
