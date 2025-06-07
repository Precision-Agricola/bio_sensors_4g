# test/calibrate_co2.py
#
from machine import SoftI2C, Pin
from utils.scd4x import SCD4X
from time import sleep

i2c = SoftI2C(scl=Pin(23), sda=Pin(31))
scd = SCD4X(i2c)

print("Reiniciando sensor...")
scd.reinit()
scd.factory_reset()

# --- Calibración forzada (si conoces el valor real de CO2, usa ese)
try:
    scd.force_calibration(415)
    print("Calibración forzada exitosa")
except Exception as e:
    print("Error en calibración:", e)

# --- Activar ASC y guardar en EEPROM
scd.self_calibration_enabled = True
print("ASC activado:", scd.self_calibration_enabled)

scd.persist_settings()
print("Configuraciones guardadas en EEPROM")

