"""Sensor reading and data transmission code

rrecisón Agrícola
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
relay3 = Pin(12, Pin.OUT)
relay4 = Pin(27, Pin.OUT)

mqtt = MQTTManager()
rtc = init_rtc()
timer = Timer(0)

# Constants
ON_DURATION = 60       # 3 horas en segundos
PRE_OFF_TIME = 5        # 5 minutos en segundos
OFF_DURATION = 60      # 3 horas en segundos

def test_all_relays():
    """Test de todos los relevadores"""
    print("Probando relevadores...")
    for relay in [relay1, relay2, relay3, relay4]:
        relay.value(1)
    time.sleep(1)
    for relay in [relay1, relay2, relay3, relay4]:
        relay.value(0)
    print("Prueba de relevadores completada")

def load_sensor_config(path="config/sensors.json"):
    """Cargar configuración de sensores"""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sensor config:", e)
        return []

def create_sensor(conf):
    """Crear instancia de sensor"""
    from sensors.base import sensor_registry
    key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
    return sensor_registry.get(key)(**conf) if key in sensor_registry else None

def test_sensors(sensor_configs):
    """Obtener lecturas de todos los sensores"""
    sensor_status = {}
    for conf in sensor_configs:
        sensor = create_sensor(conf)
        if sensor:
            reading = sensor.read()
            sensor_status[conf["name"]] = {
                "status": "OK" if reading is not None else "Error",
                "reading": reading
            }
    return sensor_status

def prepare_payload(sensor_status):
    """Crear estructura de datos para enviar"""
    return {
        "device_id": DEVICE_SERIAL["device_id"],
        "timestamp": get_current_time(rtc)[-1],
        "sensors": sensor_status,
        "system_status": "ON" if relay1.value() else "OFF"
    }

def sensor_routine():
    """Rutina de lectura y transmisión de datos"""
    try:
        sensor_configs = load_sensor_config()
        if not sensor_configs:
            return
            
        status = test_sensors(sensor_configs)
        payload = prepare_payload(status)
        
        if mqtt.publish(payload):
            print("Datos enviados exitosamente")
        else:
            print("Datos guardados en respaldo")
            
    except Exception as e:
        print("Error en rutina de sensores:", e)

def system_on(t=None):
    """Activar todo el sistema"""
    print("\n=== SISTEMA ACTIVADO ===")
    # Encender todos los relevadores
    for relay in [relay1, relay2, relay3, relay4]:
        relay.value(1)
    
    # Programar lectura de sensores antes de apagar
    timer.init(period=(ON_DURATION - PRE_OFF_TIME) * 1000, 
              mode=Timer.ONE_SHOT, 
              callback=trigger_data_transmission)

def trigger_data_transmission(t):
    """Ejecutar rutina final antes de apagar"""
    print("\nIniciando secuencia pre-apagado...")
    sensor_routine()
    # Programar apagado completo después de PRE_OFF_TIME
    timer.init(period=PRE_OFF_TIME * 1000, 
              mode=Timer.ONE_SHOT, 
              callback=system_off)

def system_off(t=None):
    """Desactivar todo el sistema"""
    print("\n=== SISTEMA DESACTIVADO ===")
    # Apagar todos los relevadores
    for relay in [relay1, relay2, relay3, relay4]:
        relay.value(0)
    
    # Programar próximo ciclo
    timer.init(period=OFF_DURATION * 1000, 
              mode=Timer.ONE_SHOT, 
              callback=system_on)

# Configuración inicial
print("Inicializando sistema...")
connect()  # Conectar a WiFi
test_all_relays()
system_on()  # Iniciar ciclo

# Bucle principal para mantener la conexión
while True:
    if not mqtt.is_connected():
        mqtt.reconnect()
    time.sleep(10)