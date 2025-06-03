from machine import I2C, Pin
from scd4x import SCD4x  # ajusta si el archivo está en otro path
import time

# Inicializa I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # ajusta pines según tu hardware
sensor = SCD4x(i2c)

# Inicia medición periódica
sensor.stop_periodic()
sensor.start_periodic()
time.sleep(5)  # espera inicial

# Lecturas simples
for i in range(3):
    if sensor.data_ready():
        co2, temp, rh = sensor.read_measurement()
        print("CO₂:", co2, "ppm | Temp:", round(temp, 2), "°C | RH:", round(rh, 1), "%")
    else:
        print("Esperando datos...")
    time.sleep(5)

