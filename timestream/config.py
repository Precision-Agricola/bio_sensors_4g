from math import sin, pi
import time
from datetime import datetime
import random
import requests
from bisect import bisect_right

# --- Configuración general ---
DEVICE_IDS = [f"ESP32_{suffix}" for suffix in ["5ED9F4", "653218", "FEWCD01", "RF2889"]]
DATABASE_NAME = "sampleDB"
TABLE_NAME = "sampleTable"

# --- Ubicación y offset por dispositivo (puedes ajustar si quieres más diferencias) ---
_LAT, _LON = 25.56316228176671, -108.47064300518863
DEVICE_OFFSETS = {
    "ESP32_5ED9F4": 0.0,
    "ESP32_653218": 0.4,
    "ESP32_FEWCD01": -0.3,
    "ESP32_RF2889": 0.6
}

# --- Caché en memoria por día ---
_temp_day_cache = {}

# --- Ruido leve ---
def __noise(scale=1.0): return random.gauss(0, scale)

# --- Temperatura interpolada con 6 puntos diarios ---
def __get_interpolated_temp(t):
    fecha = t.strftime("%Y-%m-%d")
    hora_actual = t.hour
    key = f"{fecha}"

    if key not in _temp_day_cache:
        try:
            print(f"[INFO] Requesting temperature for {fecha}...")
            time.sleep(1)  # <-- aquí
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": _LAT,
                "longitude": _LON,
                "hourly": "temperature_2m",
                "start_date": fecha,
                "end_date": fecha,
                "timezone": "auto"
            }
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()

            horas = data["hourly"]["time"]
            temps = data["hourly"]["temperature_2m"]

            indices_objetivo = [f"{fecha}T{str(h).zfill(2)}:00" for h in [0, 4, 8, 12, 16, 20]]
            hs = []
            ts = []

            for h in indices_objetivo:
                if h in horas:
                    idx = horas.index(h)
                    hs.append(int(h[11:13]))
                    ts.append(temps[idx])

            _temp_day_cache[key] = (hs, ts)
            print(f"[OK] Cached 6 temps for {fecha}: {ts}")
        except Exception as e:
            print(f"[ERROR] Failed to get temp for {fecha}: {e}")
            return 22 + __noise(1.0)

    hs, ts = _temp_day_cache[key]
    if hora_actual in hs:
        return ts[hs.index(hora_actual)]
    else:
        idx = bisect_right(hs, hora_actual)
        h1, h2 = hs[idx - 1], hs[idx % len(hs)]
        t1, t2 = ts[idx - 1], ts[idx % len(ts)]

        if h2 < h1:
            h2 += 24  # Wraparound

        factor = (hora_actual - h1) / (h2 - h1)
        interpolated = t1 + (t2 - t1) * factor
        return round(interpolated + __noise(0.3), 2)

# --- Estado aerador 3hr ON/OFF ---
def is_aerator_on(timestamp):
    return (timestamp.hour % 6) < 3

# --- Generador principal ---
def generate_sensor_data(t, device_id):
    random.seed(f"{device_id}-{t}")
    aerator_on = is_aerator_on(t)
    device_offset = DEVICE_OFFSETS.get(device_id, 0)

    base_temp = __get_interpolated_temp(t) + device_offset
    ambient_temp = round(base_temp + __noise(0.3), 2)
    rs485_temp = round(base_temp + 1.2 + __noise(0.3), 2)
    pressure_temp = round(base_temp + 0.5 + __noise(0.2), 2)

    return {
        "H2S": round(random.uniform(128, 367), 2),
        "NH3": round(random.uniform(0.026, 0.027), 5),
        "Sensor pH": {
            "ph_value": round(random.uniform(423, 454), 2)
        },
        "RS485 Sensor": {
            "rs485_temperature": rs485_temp if aerator_on else None,
            "ambient_temperature": ambient_temp if aerator_on else None,
            "level": round(random.uniform(-0.027, -0.025), 5) if aerator_on else None
        },
        "Pressure": {
            "pressure": round(random.uniform(762, 767), 4),
            "altitude": round(random.uniform(2302, 2333), 3),
            "temperature": pressure_temp
        },
        "aerator_status": "ON" if aerator_on else "OFF"
    }
