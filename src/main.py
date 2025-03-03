"""Sensor reading and data transmission code

Precisón Agrícola
Investigation and Development Department

@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025

"""
import time
import json
from machine import Pin, Timer
from calendar.get_time import init_rtc, get_current_time
import sensors.amonia.sen0567 
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901
from config.secrets import DEVICE_SERIAL, MQTT_CONFIG, WIFI_CONFIG
from local_network.mqtt import MQTTManager
from local_network.wifi import connect

# Relay configuration
relay1 = Pin(13, Pin.OUT)
relay2 = Pin(14, Pin.OUT)

# Aerator relays - Added for alternating control
relay3 = Pin(12, Pin.OUT)
relay4 = Pin(27, Pin.OUT)

mqtt = MQTTManager()

# === AERATOR CONTROL SYSTEM ===
aerator_timer = Timer(2)
aerator_active = False 

def aerator_on():
    """Enciende ambos relevadores del aireador"""
    relay3.value(1)
    relay4.value(1)
    print("Aerador ENCENDIDO (Ambos relevadores)")

def aerator_off():
    """Apaga ambos relevadores del aireador"""
    relay3.value(0)
    relay4.value(0)
    print("Aerador APAGADO")

def aerator_cycle_on(_):
    """Inicia ciclo de encendido (3 horas)"""
    aerator_on()
    # Programa el apagado en 3 horas
    Timer(3).init(period=10800000, mode=Timer.ONE_SHOT, 
                 callback=aerator_cycle_off)

def aerator_cycle_off(_):
    """Inicia ciclo de apagado (3 horas)"""
    aerator_off()
    # Programa el encendido en 3 horas
    Timer(4).init(period=10800000, mode=Timer.ONE_SHOT, 
                 callback=aerator_cycle_on)

def start_aerator_schedule():
    """Inicializa y comienza el programa del aireador"""
    aerator_off()  # Asegura que comience apagado
    aerator_cycle_on(None)  # Inicia el primer ciclo
    print("Programa del aireador iniciado: 3 horas ENCENDIDO, 3 horas APAGADO")


def test_all_relays():
    """Test de todos los relevadores"""
    print("Probando relevadores...")
    # Test de relevadores de sensores
    relay1.value(1)
    relay2.value(1)
    time.sleep(1)
    relay1.value(0)
    relay2.value(0)
    
    # Test de relevadores del aireador (ambos juntos)
    relay3.value(1)
    relay4.value(1)
    time.sleep(1)
    relay3.value(0)
    relay4.value(0)
    print("Prueba de relevadores completada")
# === END AERATOR CONTROL SYSTEM ===

# Original sensor relay functions
def activate_relays():
    """Activate both sensor relays and wait for stabilization."""
    relay1.value(1)
    relay2.value(1)
    time.sleep(2)  # Allow time for stabilization

def deactivate_relays():
    """Deactivate both sensor relays."""
    relay1.value(0)
    relay2.value(0)

def load_sensor_config(path="config/sensors.json"):
    """Load sensor configurations from a JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sensor config:", e)
        return []

def create_sensor(conf):
    """Create a sensor instance based on its configuration."""
    from sensors.base import sensor_registry  # Lazy import to avoid circular issues
    if "signal" not in conf:
        conf["signal"] = None
    key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
    sensor_cls = sensor_registry.get(key)
    if sensor_cls:
        return sensor_cls(**conf)
    print(f"Unregistered sensor: {key}")
    return None

def test_sensors(sensor_configs):
    """Test all sensors and return their status and readings."""
    sensor_status = {}
    for conf in sensor_configs:
        sensor = create_sensor(conf)
        if sensor:
            reading = sensor.read()
            sensor_status[conf["name"]] = {
                "status": "OK" if reading is not None else "Error",
                "reading": reading
            }
        else:
            sensor_status[conf["name"]] = {"status": "Unregistered", "reading": None}
    return sensor_status

def prepare_payload(sensor_status):
    """Prepare a payload with timestamp and sensor status."""
    return {
        "device_id": DEVICE_SERIAL["device_id"],
        "timestamp": time.time(),
        "sensors": sensor_status
    }

def sensor_routine():
    """Execute sensor reading and send data via MQTT."""
    sensor_configs = load_sensor_config()
    if not sensor_configs:
        print("No sensor configurations found!")
        return
    
    activate_relays()
    try:
        status = test_sensors(sensor_configs)
        payload = {
            "device_id": DEVICE_SERIAL["device_id"],
            "timestamp": time.time(),
            "sensors": status
        }
        if mqtt.publish(payload):
            print("Data sent via MQTT")
        else:
            print("Saved to backup")
    except Exception as e:
        print("Routine Error:", e)
    finally:
        deactivate_relays()
    schedule_next_run()

def schedule_next_run():
    """Schedule the next sensor routine execution at the 10th second of the next minute."""
    y, mo, d, h, m, s = get_current_time(rtc)
    seconds_until_next = (60 - s + 10) % 60  # Time until next minute's 10th second
    if seconds_until_next == 0:
        seconds_until_next = 60  # Full minute if exactly on time
    timer.init(period=seconds_until_next * 1000, mode=Timer.ONE_SHOT, callback=lambda t: sensor_routine())

def check_time(timer):
    """Check current time and trigger sensor routine at the 10th second."""
    y, mo, d, h, m, s = get_current_time(rtc)
    if s == 10:
        print(f"Starting routine at {h}:{m}:{s}")
        sensor_routine()

# Ensure WiFi is connected before starting
print("Initializing...")
wifi_connected = connect()
print(f"WiFi status: {'Connected' if wifi_connected else 'Disconnected'}")

# Test all relays
test_all_relays()

# Start aerator control system
start_aerator_schedule()

# Initialize RTC
rtc = init_rtc()
timer = Timer(0)
schedule_next_run()

# Main loop
while True:
    # Try reconnecting WiFi periodically if it's not connected
    if not wifi_connected:
        wifi_connected = connect()
        if wifi_connected:
            print("WiFi reconnected")
    time.sleep(1)
