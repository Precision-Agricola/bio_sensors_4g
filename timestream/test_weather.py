#%%
import requests
from datetime import datetime
from pytz import timezone
local_tz = timezone("America/Mazatlan")

LAT = 25.78758584457698
LON = -108.89569650966546
#%%
def get_current_temp():
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.now().astimezone(local_tz)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
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
    hora_clave = f"{fecha}T{str(hora_actual).zfill(2)}:00"

    if hora_clave in horas:
        idx = horas.index(hora_clave)
        return temps[idx]
    else:
        return "No hay temperatura exacta para esta hora."

try:
    print("Temperatura actual:", get_current_temp(), "°C")
except Exception as e:
    print("[ERROR]", e)
