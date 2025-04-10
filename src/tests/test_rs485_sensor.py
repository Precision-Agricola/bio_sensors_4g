# test_rs485_sensor.py

import time
from sensors.rs485.rs485_sensor import RS485Sensor

def log_to_file(data, file_path="rs485_log.txt"):
    try:
        with open(file_path, "a") as f:
            f.write(data + "\n")
    except Exception as e:
        print("Error writing file:", e)

# Crear instancia del sensor manualmente
sensor = RS485Sensor(
    name="RS485 Sensor",
    model="RS485_SENSOR",
    protocol="MODBUS",
    vin=3.3,
    signal=1,
    bus_num=2,
    address=1
)

# Inicializar hardware
sensor._init_hardware()

# Leer y guardar
reading = sensor._read_implementation()
timestamp = time.time()
line = f"{timestamp}, {reading}"
print(line)
log_to_file(line)
