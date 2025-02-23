import time
import json
from machine import Pin
from sensors.base import sensor_registry

# Importar módulos para registrar sensores
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901

# Configuración de relevadores
relay1 = Pin(13, Pin.OUT)
relay2 = Pin(14, Pin.OUT)

def activate_relays():
    relay1.value(1)
    relay2.value(1)
    time.sleep(2)  # Esperar estabilización de los sensores

def deactivate_relays():
    relay1.value(0)
    relay2.value(0)

def load_sensor_config(path="config/sensors.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error al leer la configuración de sensores:", e)
        return []

def create_sensor(conf):
    # Asegurarse de que 'signal' esté presente, incluso si es None.
    if "signal" not in conf:
        conf["signal"] = None
    key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
    sensor_cls = sensor_registry.get(key)
    if sensor_cls:
        return sensor_cls(**conf)
    else:
        print(f"Sensor no registrado: {key}")
        return None

def test_sensors(sensor_configs):
    sensor_status = {}
    for conf in sensor_configs:
        sensor = create_sensor(conf)
        if sensor:
            reading = sensor.read()
            if reading is not None:
                sensor_status[conf["name"]] = {"status": "OK", "reading": reading}
            else:
                sensor_status[conf["name"]] = {"status": "Error", "reading": None}
        else:
            sensor_status[conf["name"]] = {"status": "No registrado", "reading": None}
    return sensor_status

def prepare_payload(sensor_status):
    payload = {
        "timestamp": time.time(),
        "sensors": sensor_status
    }
    return payload

def main():
    sensor_configs = load_sensor_config()
    if not sensor_configs:
        print("¡No se encontró configuración de sensores!")
        return

    activate_relays()
    status = test_sensors(sensor_configs)
    deactivate_relays()

    payload = prepare_payload(status)
    print("Payload:", payload)
    print("JSON Payload:", json.dumps(payload))

if __name__ == "__main__":
    main()
