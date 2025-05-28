# client/config/sensors_config.py

import json
from sensors.base import sensor_registry
from utils.logger import log_message


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
                log_message(f"Skipping unknown sensor: {model} ({protocol})")
        log_message(f"Loaded Sensors {sensors}")
        return sensors
    except Exception as e:
        log_message(f"Error loading sensor config: {str(e)}")
        return []
