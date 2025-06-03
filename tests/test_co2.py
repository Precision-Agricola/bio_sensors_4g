from machine import I2C, Pin
from utils.scd4x import SCD4x
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # ajusta pines según tu hardware
scd = SCD4x(i2c)

scd.stop_periodic()
scd.reinit()
scd.start_periodic()

print("Esperando datos del sensor...")
time.sleep(10)

if scd.data_ready():
    co2, temp, hum = scd.read_measurement()
    print("CO2:", co2, "ppm")
    print("Temp:", temp, "°C")
    print("Humedad:", hum, "%")
else:
    print("Datos no listos aún.")

