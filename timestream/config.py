from math import sin, pi
import time
from datetime import datetime
import random
import requests
from bisect import bisect_right

DEVICE_IDS = [f"ESP32_{suffix}" for suffix in ["3002EC", "5DAEC4", "5D99C8", "2E57D0"]]
DATABASE_NAME = "sampleDB"
TABLE_NAME = "sampleTable"

_LAT, _LON = 25.78758584457698, -108.89569650966546
DEVICE_OFFSETS = {
    "ESP32_5ED9F4": 0.0,
    "ESP32_653218": 0.4,
    "ESP32_FEWCD01": -0.3,
    "ESP32_RF2889": 0.6
}

_temp_day_cache = {}

# --- Ruido leve ---
def __noise(scale=1.0): return random.gauss(0, scale)

# --- Temperatura interpolada ---
def get_interpolated_temp(t):
    fecha = t.strftime("%Y-%m-%d")
    hora_actual = t.hour
    key = f"{fecha}"

    if key not in _temp_day_cache:
        try:
            print(f"[INFO] Requesting temperature for {fecha}...")
            time.sleep(1)
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": _LAT,
                "longitude": _LON,
                "hourly": "temperature_2m",
                "start_date": fecha,
                "end_date": fecha,
                "timezone": "America/Mexico_City"
            }
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()

            horas = data["hourly"]["time"]
            temps = data["hourly"]["temperature_2m"]
            horas_interes = [5, 6, 7, 9, 11, 13, 15, 16, 18, 21]
            indices_objetivo = [f"{fecha}T{str(h).zfill(2)}:00" for h in horas_interes]
            hs = []
            ts = []

            for h in indices_objetivo:
                if h in horas:
                    idx = horas.index(h)
                    hs.append(int(h[11:13]))
                    ts.append(temps[idx])

            _temp_day_cache[key] = (hs, ts)
            print(f"[OK] Cached {len(ts)} temps for {fecha}: {ts}")
        except Exception as e:
            print(f"[ERROR] Failed to get temp for {fecha}: {e}")
            _temp_day_cache[key] = ([], [])  # evita reintentos múltiples
            return 22 + __noise(1.0)

    hs, ts = _temp_day_cache[key]
    if not hs:
        return 22 + __noise(1.0)

    if hora_actual in hs:
        return ts[hs.index(hora_actual)]
    else:
        idx = bisect_right(hs, hora_actual)
        h1, h2 = hs[idx - 1], hs[idx % len(hs)]
        t1, t2 = ts[idx - 1], ts[idx % len(ts)]
        if h2 < h1:
            h2 += 24
        factor = (hora_actual - h1) / (h2 - h1)
        interpolated = t1 + (t2 - t1) * factor
        return round(interpolated + __noise(0.3), 2)

def is_aerator_on(timestamp):
    return (timestamp.hour % 6) < 3

def generate_sensor_data(t, device_id, external_temp=None):
    random.seed(f"{device_id}-{t}")
    aerator_on = is_aerator_on(t)
    device_offset = DEVICE_OFFSETS.get(device_id, 0)

    if external_temp is None:
        external_temp = get_interpolated_temp(t)

    base_temp = external_temp + device_offset
    ambient_temp = round(base_temp + __noise(0.3), 2)
    rs485_temp = round(base_temp + 1.2 + __noise(0.3), 2)
    pressure_temp = round(base_temp + 0.5 + __noise(0.2), 2)

    return {
        "H2S": round(random.uniform(298, 367), 2),
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

