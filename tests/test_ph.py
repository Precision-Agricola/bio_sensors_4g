# tests/test_ph.py

from sensors.ph.ph_sensor import PHSensor

ph = PHSensor()

try:
    value = ph.read()
    print(f"Lectura pH ({ph.name}): {value}")
except Exception as e:
    print("Error al leer sensor de pH:", e)

