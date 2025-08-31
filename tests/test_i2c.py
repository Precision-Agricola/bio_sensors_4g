# tests/test_i2c.py
#
# Escanea el bus I²C y, si detecta sensores conocidos,
# imprime una lectura rápida de cada uno.
# Versión corregida manteniendo la estructura original.

from machine import Pin, SoftI2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN
import time
from time import sleep

# ───────────────── Mapeo de sensores ──────────────────
# addr -> (nombre, función de lectura)
# La función toma el objeto i2c y la dirección, y devuelve un dict con lecturas.
def _read_bmp390(i2c, addr):
    from utils.micropython_bmpxxx.bmpxxx import BMP390
    bmp = BMP390(i2c=i2c, address=addr)
    return {
        "pressure_hPa": round(bmp.pressure, 2),
        "temperature_°C": round(bmp.temperature, 2),
        "altitude_m": round(bmp.altitude, 2),
    }

def _read_scd41(i2c, addr):
    """
    Función corregida para usar los nombres de método correctos:
    'start_periodic' y 'stop_periodic'.
    """
    from utils.scd4x import SCD4x
    scd = SCD4x(i2c)
    
    # Detener cualquier medición anterior para un inicio limpio.
    scd.stop_periodic()
    sleep(0.5)

    # Iniciar medición periódica (nombre de método CORREGIDO).
    scd.start_periodic()
    
    # Esperar el tiempo necesario para la primera lectura.
    sleep(5)
    
    if scd.data_ready():
        co2, temp, hum = scd.read_measurement()
        # Detener medición para ahorrar energía.
        scd.stop_periodic()
        return {
            "co2_ppm": co2,
            "temperature_°C": round(temp, 2),
            "humidity_%": round(hum, 1),
        }
    
    # Asegurarse de detener el sensor si los datos no están listos.
    scd.stop_periodic()
    return {"note": "Datos no listos"}

def _read_ads1115(i2c, addr):
    from utils.ads1x15 import ADS1115
    adc = ADS1115(i2c, address=addr)
    return {
        "nh3_raw": adc.read(rate=4, channel1=1),
        "h2s_raw": adc.read(rate=4, channel1=0),
    }

SENSORS = {
    0x76: ("BMP390", _read_bmp390),
    0x77: ("BMP390", _read_bmp390),
    0x62: ("SCD41",  _read_scd41),
    0x48: ("ADS1115", _read_ads1115),
}

# ────────────────────── Main ───────────────────────────
def main():
    """
    Función principal que inicializa, comprueba y escanea el bus I2C.
    """
    print("=== Guía rápida de cableado I²C ===")
    print(f"  • SCL  → pin {I2C_SCL_PIN}")
    print(f"  • SDA  → pin {I2C_SDA_PIN}")
    print("  • VCC  → 3.3V (o 5V según sensor)")
    print("  • GND  → GND")
    print("\nComprobación de líneas I²C:")

    scl_pin = Pin(I2C_SCL_PIN, Pin.IN, Pin.PULL_UP)
    sda_pin = Pin(I2C_SDA_PIN, Pin.IN, Pin.PULL_UP)
    
    time.sleep(0.1)

    scl_status = "OK" if scl_pin.value() == 1 else "FALLO (línea en bajo)"
    sda_status = "OK" if sda_pin.value() == 1 else "FALLO (línea en bajo)"
    
    print(f"  SCL idle alto: {scl_status}")
    print(f"  SDA idle alto: {sda_status}")
    print("-" * 30)

    if scl_pin.value() == 0 or sda_pin.value() == 0:
        print("¡Atención! Una o ambas líneas I2C están en bajo.")
        print("Verifica el cableado, las resistencias pull-up y la alimentación.")
        return

    i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    
    print("\nBuscando dispositivos I2C...")
    devices = i2c.scan()

    if not devices:
        print("No se encontraron dispositivos I2C.")
        return

    print("Dispositivos I2C encontrados:")
    for addr in devices:
        sensor = SENSORS.get(addr)
        if not sensor:
            print(f" - 0x{addr:02X}: Dispositivo desconocido")
            continue

        name, reader = sensor
        print(f" - 0x{addr:02X}: {name} →", end="")
        try:
            data = reader(i2c, addr)
            print(f" {data}")
        except Exception as e:
            print(f" ERROR: {e}")

if __name__ == "__main__":
    main()

