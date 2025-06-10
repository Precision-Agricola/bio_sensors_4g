# tests/test_ph.py

from sensors.ph.ph_sensor import PHSensor
import time

ph = PHSensor()

try:
    for i in range(10):
        lectura = ph.read()  # Devuelve {"ph_value": valor}
        valor = lectura["ph_value"] / 111.74  # Normalización arbitraria
        print(f"Muestra {i+1}: pH = {valor:.2f}")
        time.sleep(0.1)

except Exception as e:
    print("Error al leer sensor de pH:", e)