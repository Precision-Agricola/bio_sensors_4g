from machine import SoftI2C, Pin
from time import sleep
from utils.scd4x import SCD4X

i2c = SoftI2C(scl=Pin(23), sda=Pin(31))
scd = SCD4X(i2c)

print("Iniciando sensor...")
scd.stop_periodic_measurement()
scd.reinit()
scd.factory_reset()
scd.start_periodic_measurement()

sleep(10)

if scd.data_ready:
    print("CO2:", scd.CO2, "ppm")
    print("Temp:", scd.temperature, "°C")
    print("Humedad:", scd.relative_humidity, "%")
else:
    print("Datos no listos aún")
