from machine import I2C, Pin
from utils.scd4x import SCD4x
import time

i2c = I2C(0, scl=Pin(23), sda=Pin(21))
sensor = SCD4x(i2c)

sensor.stop_periodic()
sensor.start_periodic()
time.sleep(5)

for i in range(3):
    if sensor.data_ready():
        co2, temp, rh = sensor.read_measurement()
        print("CO₂:", co2, "ppm | Temp:", round(temp, 2), "°C | RH:", round(rh, 1), "%")
    else:
        print("Esperando datos...")
    time.sleep(5)

