# tests/test_co2.py

from machine import SoftI2C, Pin
from utils.scd4x import SCD4x
from time import sleep

i2c = SoftI2C(scl=Pin(23), sda=Pin(31))
scd = SCD4x(i2c)

print("Iniciando sensor...")
scd.stop_periodic()
scd.start_periodic()

print("Esperando datos...")
sleep(10)

if scd.data_ready():
    try:
        co2, temp, hum = scd.read_measurement()
        print("CO2:", co2, "ppm")
        print("Temp:", temp, "°C")
        print("Humedad:", hum, "%")
    except Exception as e:
        print("Error al leer medición:", e)
else:
    print("Datos no listos aún")

