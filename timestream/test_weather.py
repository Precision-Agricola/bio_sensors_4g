#%%
from datetime import datetime
from pytz import timezone
from config import get_interpolated_temp  # importar desde config.py

#%%
local_tz = timezone("America/Mazatlan")
now = datetime.now().astimezone(local_tz)

try:
    temperatura = get_interpolated_temp(now)
    print("Temperatura actual (interpolada):", temperatura, "°C")
except Exception as e:
    print("[ERROR]", e)
