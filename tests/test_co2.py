# tests/test_co2.py

from machine import SoftI2C, Pin
from utils.scd4x import SCD4X
from time import sleep

i2c = SoftI2C(scl=Pin(23), sda=Pin(31))
scd = SCD4X(i2c)

scd.start_periodic_measurement()
print("Esperando datos...")

sleep(10)  # espera inicial

if scd.data_ready:
    print("CO2:", scd.CO2, "ppm")
    print("Temp:", scd.temperature, "°C")
    print("Humedad:", scd.relative_humidity, "%")
else:
    print("Datos no listos aún")

