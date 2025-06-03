from machine import Pin, I2C
from time import sleep
from client.utils.scd4x import SCD4x  # ajusta ruta si es necesario

# I2C setup (ajusta pines si usas otros)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
scd = SCD4x(i2c)

# Reinicio del sensor
scd.stop_periodic()
scd.reinit()
sleep(1)

# Activar autocalibración y guardar en EEPROM
scd.set_auto_calibration(True)
scd.persist_settings()

# Verificar autocalibración
print("Auto-calibración activa:", scd.get_auto_calibration())

# Leer número de serie
try:
    sn = scd.read_serial_number()
    print("Serial:", hex(sn))
except Exception as e:
    print("Error leyendo serial:", e)

# Iniciar lectura periódica
scd.start_periodic()
print("Esperando datos del sensor...")
sleep(10)  # espera inicial

# Lecturas continuas
for i in range(5):
    if scd.data_ready():
        try:
            co2, temp, hum = scd.read_measurement()
            print(f"[{i+1}] CO₂: {co2} ppm | T: {temp:.2f}°C | RH: {hum:.2f}%")
        except Exception as e:
            print("Error de lectura:", e)
    else:
        print(f"[{i+1}] Datos no listos")
    sleep(5)

