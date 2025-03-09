"""Sensor reading and data transmission code

Precisón Agrícola
Investigation and Development Department

@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025
Modified: March 2025 - Sistema de timer unificado

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
relay1 = Pin(13, Pin.OUT)  # Sensor relay 1
relay2 = Pin(14, Pin.OUT)  # Sensor relay 2
relay3 = Pin(12, Pin.OUT)  # Aerator relay 1
relay4 = Pin(27, Pin.OUT)  # Aerator relay 2

mqtt = MQTTManager()

# === UNIFIED CONTROL SYSTEM ===
system_timer = Timer(1)
# Estado del sistema: 0 = apagado, 1 = encendido, 2 = lectura de sensores
system_state = 0

# Constantes de tiempo (en milisegundos)
ACTIVE_TIME = 60 * 1000  # 3 horas encendido
INACTIVE_TIME = 60 * 1000  # 3 horas apagado
SENSOR_READ_BEFORE_OFF = 5 * 1000  # 5 minutos antes de apagar

def activate_all():
    """Activa el aireador y energiza los sensores"""
    # Activar relevadores de sensores
    relay1.value(1)
    relay2.value(1)
    # Activar relevadores del aireador
    relay3.value(1)
    relay4.value(1)
    print("Sistema ACTIVADO: Aireador y sensores energizados")

def deactivate_all():
    """Apaga el aireador y desactiva los sensores"""
    # Desactivar relevadores de sensores
    relay1.value(0)
    relay2.value(0)
    # Desactivar relevadores del aireador
    relay3.value(0)
    relay4.value(0)
    print("Sistema DESACTIVADO: Aireador y sensores apagados")

def system_control(timer):
    """Función de control del sistema basada en estados"""
    global system_state
    
    if system_state == 0:
        # Cambio de estado: apagado -> encendido
        system_state = 1
        activate_all()
        # Programar lectura de sensores 5 minutos antes de finalizar
        system_timer.init(period=ACTIVE_TIME - SENSOR_READ_BEFORE_OFF, 
                         mode=Timer.ONE_SHOT, callback=system_control)
        print(f"Sistema encendido por {(ACTIVE_TIME - SENSOR_READ_BEFORE_OFF) // 60000} minutos hasta lectura de sensores")
        
    elif system_state == 1:
        # Cambio de estado: encendido -> lectura de sensores
        system_state = 2
        print("Realizando lectura de sensores antes de apagar...")
        # Realizar lectura de sensores y enviar datos
        sensor_routine()
        # Programar apagado después de la lectura
        system_timer.init(period=SENSOR_READ_BEFORE_OFF, 
                         mode=Timer.ONE_SHOT, callback=system_control)
        print(f"Sistema se apagará en {SENSOR_READ_BEFORE_OFF // 60000} minutos")
        
    elif system_state == 2:
        # Cambio de estado: lectura de sensores -> apagado
        system_state = 0
        deactivate_all()
        # Programar próximo encendido
        system_timer.init(period=INACTIVE_TIME, 
                         mode=Timer.ONE_SHOT, callback=system_control)
        print(f"Sistema apagado por {INACTIVE_TIME // 60000} minutos")

def test_all_relays():
    """Test de todos los relevadores"""
    print("Probando relevadores...")
    # Test de relevadores de sensores
    relay1.value(1)
    relay2.value(1)
    time.sleep(1)
    relay1.value(0)
    relay2.value(0)
    
    # Test de relevadores del aireador
    relay3.value(1)
    relay4.value(1)
    time.sleep(1)
    relay3.value(0)
    relay4.value(0)
    print("Prueba de relevadores completada")
# === END UNIFIED CONTROL SYSTEM ===

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
    """Prepare a payload with timestamp, sensor status, and aerator status."""
    return {
        "device_id": DEVICE_SERIAL["device_id"],
        "timestamp": time.time(),
        "sensors": sensor_status,
        "aerator_status": {
            "relay3": relay3.value(),
            "relay4": relay4.value()
        }
    }

def sensor_routine():
    """Execute sensor reading and send data via MQTT."""
    sensor_configs = load_sensor_config()
    if not sensor_configs:
        print("No sensor configurations found!")
        return
    
    # No necesitamos activar los relés aquí ya que ya están encendidos por el sistema unificado
    try:
        status = test_sensors(sensor_configs)
        payload = prepare_payload(status)
        
        if mqtt.publish(payload):
            print("Datos enviados por MQTT exitosamente")
        else:
            print("Datos guardados en respaldo local")
    except Exception as e:
        print("Error en la rutina de sensores:", e)

# Ensure WiFi is connected before starting
print("Inicializando sistema...")
wifi_connected = connect()
print(f"Estado de WiFi: {'Conectado' if wifi_connected else 'Desconectado'}")

# Test all relays
test_all_relays()

# Inicializar RTC
rtc = init_rtc()

# Iniciar el sistema unificado
print("Iniciando sistema de control unificado...")
# Asegurar que todo comience apagado
deactivate_all()
# Iniciar el ciclo inmediatamente (comienza activando todo)
system_control(None)

# Main loop
while True:
    # Try reconnecting WiFi periodically if it's not connected
    if not wifi_connected:
        wifi_connected = connect()
        if wifi_connected:
            print("WiFi reconectado")
    time.sleep(1)
