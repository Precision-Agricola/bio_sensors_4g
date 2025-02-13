import json

def load_sensor_config(config_file='config/sensors.json'):
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        sensors = []
        for item in config:
            key = (item.get('model'), item.get('protocol'))
            sensor_cls = sensor_registry.get(key)
            if sensor_cls:
                sensors.append(sensor_cls(**item))
            else:
                print('Skipping unknown sensor:', item.get('model'))
        return sensors
    except:
        print('Error loading sensor config')
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
