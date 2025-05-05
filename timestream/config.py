# config.py

from math import sin, pi
from datetime import datetime

def __noise(t): return sin(t.timestamp() / 600.0)
def __day_night_cycle(t): return sin((t.hour + t.minute / 60) / 24 * 2 * pi)

DEVICE_IDS = [f"ESP32_{suffix}" for suffix in ["5ED9F4", "653218", "FEWCD01", "RF2889"]]

DATABASE_NAME = "sampleDB"
TABLE_NAME = "sampleTable"

def is_aerator_on(timestamp):
    cycle_position = (timestamp.hour % 6) // 3  # 0 or 1
    return cycle_position == 0  # First 3 hours ON, next 3 hours OFF

def generate_sensor_data(t):
    aerator_on = is_aerator_on(t)
    return {
        "H2S": round(250 + 20 * __noise(t), 2),
        "NH3": round(5 + 3 * __noise(t), 2),
        "Sensor pH": {
            "ph_value": round(7 + 0.7 * __noise(t), 2)
        },
        "RS485 Sensor": {
            "rs485_temperature": round(270 + 3 * __day_night_cycle(t), 2) if aerator_on else None,
            "ambient_temperature": round(25 + 4 * __day_night_cycle(t), 2) if aerator_on else None,
            "level": round(-0.02 + 0.01 * __noise(t), 5) if aerator_on else None
        },
        "Pressure": {
            "pressure": round(760 + 5 * __noise(t), 4),
            "altitude": round(2300 + 30 * __noise(t), 3),
            "temperature": round(24 + 5 * __day_night_cycle(t), 5)
        },
        "aerator_status": "ON" if aerator_on else "OFF"
    }
