import requests

def obtener_temperatura(lat, lon, fecha, hora):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "start_date": fecha,
        "end_date": fecha,
        "timezone": "auto"
    }
    r = requests.get(url, params=params)
    datos = r.json()
    horas = datos["hourly"]["time"]
    temperaturas = datos["hourly"]["temperature_2m"]
    try:
        idx = horas.index(f"{fecha}T{hora}:00")
        return temperaturas[idx]
    except ValueError:
        return None

print(obtener_temperatura(25.56316228176671, -108.47064300518863, "2025-04-11", "06"))
