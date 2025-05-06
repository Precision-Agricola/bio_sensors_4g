# config.py

from math import sin, pi
from datetime import datetime
import random

def __noise(t): return sin(t.timestamp() / 600.0)
def __day_night_cycle(t): return sin((t.hour + t.minute / 60) / 24 * 2 * pi)

DEVICE_IDS = [f"ESP32_{suffix}" for suffix in ["5ED9F4", "653218", "FEWCD01", "RF2889"]]

DATABASE_NAME = "sampleDB"
TABLE_NAME = "sampleTable"

def is_aerator_on(timestamp):
    cycle_position = (timestamp.hour % 6) // 3  # 0 or 1
    return cycle_position == 0  # First 3 hours ON, next 3 hours OFF

def generate_sensor_data(t, device_id):
    random.seed(f"{device_id}-{t}")  # Variación consistente por dispositivo y hora
    aerator_on = is_aerator_on(t)

    temp_day_cycle = 24 + 5 * __day_night_cycle(t)  # Solo temperatura

    return {
        "H2S": round(240 + random.uniform(-15, 15), 2),
        "NH3": round(3 + random.uniform(-2, 4), 2),
        "Sensor pH": {
            "ph_value": round(6.5 + random.uniform(-1, 1), 2)
        },
        "RS485 Sensor": {
            "rs485_temperature": round(268 + random.uniform(-5, 5), 2) if aerator_on else None,
            "ambient_temperature": round(22 + random.uniform(-2, 3), 2) if aerator_on else None,
            "level": round(-0.025 + random.uniform(-0.01, 0.01), 5) if aerator_on else None
        },
        "Pressure": {
            "pressure": round(758 + random.uniform(-3, 3), 4),
            "altitude": round(2290 + random.uniform(-20, 20), 3),
            "temperature": round(temp_day_cycle, 2)
        },
        "aerator_status": "ON" if aerator_on else "OFF"
    }
