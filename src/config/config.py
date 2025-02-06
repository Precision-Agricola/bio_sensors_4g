import json
from src.sensors.base import _sensor_registry

def load_config(config_file='src/config/sensors.json'):
    with open(config_file) as f:
        config = json.load(f)
    
    sensors = []
    for item in config.get('sensors', []):
        key = (item.get('model'), item.get('protocol'))
        sensor_cls = _sensor_registry.get(key)
        if sensor_cls is None:
            print(f"Sensor {item.get('model')} with protocol {item.get('protocol')} is not registered. Skipping.")
            continue
        sensors.append(sensor_cls(**item))
    
    return sensors
