# client/readings/sensor_reader.py

from utils.logger import log_message
from utils.ads1x15 import ADS1115
from utils.micropython_bmpxxx.bmpxxx import BMP390
from machine import Pin, SoftI2C
import time

# Config I2C pins
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

def read_i2c_sensors():
    readings = {}
    try:
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))

        # BMP390 (assume 0x77 or 0x76)
        bmp = None
        for addr in [0x77, 0x76]:
            try:
                bmp = BMP390(i2c=i2c, address=addr)
                readings['Pressure'] = {
                    "pressure": bmp.pressure,
                    "temperature": bmp.temperature,
                    "altitude": bmp.altitude
                }
                break
            except:
                continue

        # ADS1115 channels (NH3 on CH1, H2S on CH0)
        try:
            adc = ADS1115(i2c)
            readings['NH3'] = adc.read(rate=4, channel1=1)
            readings['H2S'] = adc.read(rate=4, channel1=0)
        except Exception as e:
            log_message("ADS1115 read error", e)

    except Exception as e:
        log_message("I2C read error", e)
    return readings

def read_analog_sensors():
    from sensors.ph.ph_sensor import PHSensor
    try:
        ph_sensor = PHSensor()
        value = ph_sensor.read()
        return {ph_sensor.name: value}
    except Exception as e:
        log_message("Analog sensor read error", e)
        return {}

def read_rs485_sensors():
    from sensors.rs485.rs485_sensor import RS485Sensor
    try:
        sensor = RS485Sensor()
        return {"RS485 Sensor": sensor.read()}
    except Exception as e:
        log_message("RS485 sensor read error", e)
        return {}

def get_timestamp():
    from calendar.rtc_manager import RTCManager
    try:
        rtc = RTCManager()
        t = rtc.get_time_tuple()
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*t[:6]) if t else "RTC_READ_ERROR"
    except:
        return "RTC_UNAVAILABLE"

class SensorReader:
    def __init__(self):
        self.last_readings = {}

    def read_sensors(self, aerator_state=None):
        readings = {}
        readings.update(read_i2c_sensors())
        readings.update(read_analog_sensors())
        # readings.update(read_rs485_sensors())

        timestamp = get_timestamp()
        self.last_readings = {
            "timestamp": timestamp,
            "data": readings
        }

        if aerator_state is not None:
            self.last_readings["aerator_status"] = "ON" if aerator_state else "OFF"

        return self.last_readings

    def get_last_readings(self):
        return self.last_readings
