from machine import Pin, I2C
from time import sleep
from utils.scd4x import SCD4x

i2c = I2C(0, scl=Pin(23), sda=Pin(21))
sensor = SCD4x(i2c)

# Activar auto calibración
sensor.set_auto_calibration(True)
print("Auto calibración activada:", sensor.get_auto_calibration())

# Iniciar lectura periódica
sensor.stop_periodic()
sensor.reinit()
sleep(1)
sensor.start_periodic()

# Esperar a que se estabilice y hacer lecturas
sleep(10)
for i in range(5):
    if sensor.data_ready():
        co2, temp, hum = sensor.read_measurement()
        print("CO2:", co2, "ppm | Temp:", temp, "°C | Hum:", hum, "%")
    else:
        print("Esperando datos...")
    sleep(5)

