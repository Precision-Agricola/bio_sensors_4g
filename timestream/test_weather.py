from datetime import datetime
from zoneinfo import ZoneInfo
from config import get_interpolated_temp  # importar desde config.py

#%%
local_tz = ZoneInfo("America/Mazatlan")
now = datetime.now().astimezone(local_tz)

print(f"[DEBUG] Hora local Mazatlán: {now.isoformat()}")

try:
    temperatura = get_interpolated_temp(now)
    print("Temperatura actual (interpolada):", temperatura, "°C")
except Exception as e:
    print("[ERROR]", e)
