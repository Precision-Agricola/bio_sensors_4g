import time
import json
from config.config import I2C_SCL_PIN, I2C_SDA_PIN
from machine import Pin
from readings.i2c_readings import read_i2c_sensors
from readings.analog_readings import read_analog_sensors
from utils.uart import uart  # Usa definición UART de utils

print("🚀 Iniciando prueba E2E...")

# --- 1. Leer archivo de configuración (modo de operación, pines, etc.)
try:
    import config.runtime as config
    mode = config.get_mode()
    print(f"📄 Modo de operación detectado: {mode}")
except Exception as e:
    print(f"❌ Error leyendo configuración: {e}")

# --- 2. Test de encendido/apagado de pines (relays / aerators)
try:
    pomp = Pin(12, Pin.OUT)
    aer_a = Pin(33, Pin.OUT)
    aer_b = Pin(4, Pin.OUT)

    pomp.on()
    aer_a.on()
    aer_b.off()
    print("✅ Pines encendidos: pomp (12), aerator A (33 ON), B (4 OFF)")
    time.sleep(1)

    pomp.off()
    aer_a.off()
    aer_b.on()
    print("✅ Pines invertidos: pomp (12 OFF), aerator A (33 OFF), B (4 ON)")
    time.sleep(1)

    pomp.off()
    aer_a.off()
    aer_b.off()
except Exception as e:
    print(f"❌ Error controlando pines: {e}")

# --- 3. Lectura de sensores I2C
i2c_data = {}
try:
    print("📡 Leyendo sensores I2C...")
    i2c_data = read_i2c_sensors()
    print("✅ Lectura I2C:", i2c_data)
except Exception as e:
    print(f"❌ Error sensores I2C: {e}")

# --- 4. Lectura de sensores analógicos
analog_data = {}
try:
    print("📡 Leyendo sensores analógicos...")
    analog_data = read_analog_sensors()
    print("✅ Lectura analógica:", analog_data)
except Exception as e:
    print(f"❌ Error sensores analógicos: {e}")

# --- 5. Crear payload
payload = {
    "device_id": "CLIENT-TEST-01",
    "timestamp": time.time(),
    "system_mode": "pruebas_e2e",
    "i2c": i2c_data,
    "analog": analog_data
}
print("📦 Payload generado:")
print(json.dumps(payload))

# --- 6. Enviar payload al servidor por UART directamente
try:
    uart.write(json.dumps(payload) + "\n")
    print("📤 Payload enviado por UART al servidor")
except Exception as e:
    print(f"❌ Error enviando por UART: {e}")

print("✅ Prueba E2E completada")
