# client/readings/i2c_readings.py

from utils.logger import log_message
from machine import Pin, SoftI2C
from config.config import I2C_SCL_PIN, I2C_SDA_PIN
from time import sleep

def read_i2c_sensors():
    readings = {}

    try:
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    except Exception as e:
        log_message("Error inicializando bus I2C", e)
        return readings

    # --- Sensor BMP390 (presión, temperatura, altitud) ---
    try:
        from utils.micropython_bmpxxx.bmpxxx import BMP390
        bmp = None
        for addr in [0x77, 0x76]:
            try:
                bmp = BMP390(i2c=i2c, address=addr)
                readings["BMP390"] = {
                    "pressure": bmp.pressure,
                    "temperature": bmp.temperature,
                    "altitude": bmp.altitude
                }
                break
            except:
                continue
        if bmp is None:
            log_message("No se detectó sensor BMP390 en las direcciones 0x77/0x76")
    except Exception as e:
        log_message("Error leyendo BMP390", e)

    # --- Sensor SCD41 (CO2, temperatura, humedad) ---
    try:
        from utils.scd4x import SCD4x
        scd = SCD4x(i2c)
        scd.start_periodic()
        sleep(5)
        if scd.data_ready():
            co2, temp, hum = scd.read_measurement()
            readings["SCD41"] = {
                "co2_scd": co2,
                "temperature_scd": temp,
                "humidity_scd": hum
            }
        else:
            log_message("SCD41: Datos no listos")
    except Exception as e:
        log_message("Error leyendo SCD41", e)

    # --- Sensor ADS1115 (NH3 canal 1, H2S canal 0) ---
    try:
        from utils.ads1x15 import ADS1115
        adc = ADS1115(i2c)
        readings["NH3"] = adc.read(rate=4, channel1=1)
        readings["H2S"] = adc.read(rate=4, channel1=0)
    except Exception as e:
        log_message("Error leyendo ADS1115", e)

    # --- Agrega aquí más sensores I2C manualmente ---
    # try:
    #     from sensors.i2c.xyz_sensor import XYZSensor
    #     xyz = XYZSensor(i2c)
    #     readings["XYZ"] = xyz.read()
    # except Exception as e:
    #     log_message("Error leyendo sensor XYZ", e)

    if not readings:
        log_message("No se obtuvo lectura de sensores I2C")

    return readings
