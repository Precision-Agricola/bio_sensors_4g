from machine import I2C, Pin
from utils.scd4x import SCD4X
from time import sleep

i2c = I2C(0, scl=Pin(23), sda=Pin(21))
sensor = SCD4X(i2c)

# --- Reinit y start ---
sensor.stop_periodic_measurement()
sensor.reinit()
sleep(1)
sensor.start_periodic_measurement()
sleep(10)  # espera obligatoria

# --- Serial check ---
try:
    print("Serial:", sensor.serial_number)
except Exception as e:
    print("Error leyendo número de serie:", e)

# --- Self test ---
try:
    sensor.self_test()
    print("Self test OK")
except Exception as e:
    print("Self test failed:", e)

# --- Lecturas de prueba ---
for i in range(5):
    if sensor.data_ready:
        print("Lectura", i+1)
        print("CO2:", sensor.CO2)
        print("Temp:", sensor.temperature)
        print("RH:", sensor.relative_humidity)
    else:
        print("Datos no listos")
    sleep(5)

# --- Fuerza calibración a 400 ppm (opcional) ---
try:
    sensor.force_calibration(400)
    print("Recalibración forzada OK")
except Exception as e:
    print("Error en recalibración:", e)

