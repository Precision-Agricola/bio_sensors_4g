from machine import Pin, I2C
from time import sleep
from utils.scd4x import SCD4x  # asegúrate de que el path sea correcto

# --- Inicializar I2C y sensor ---
i2c = I2C(0, scl=Pin(23), sda=Pin(21))
sensor = SCD4x(i2c)

# --- Detener medición previa, reiniciar, y configurar auto-calibración ---
sensor.stop_periodic()
sensor.reinit()
sleep(1)

sensor.set_auto_calibration(True)
print("Auto-calibración activada:", sensor.get_auto_calibration())

sensor.persist_settings()
print("Configuración persistente guardada")

# --- Iniciar medición periódica ---
sensor.start_periodic()
print("Esperando datos...")

# --- Esperar estabilidad y leer varias veces ---
sleep(10)
for i in range(5):
    if sensor.data_ready():
        co2, temp, hum = sensor.read_measurement()
        print(f"[{i+1}] CO2: {co2} ppm | Temp: {temp:.2f} °C | RH: {hum:.2f} %")
    else:
        print(f"[{i+1}] Aún no hay datos listos")
    sleep(5)

