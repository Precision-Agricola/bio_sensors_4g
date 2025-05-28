# client/readings/i2c_reader.py

import time
from machine import Pin, SoftI2C
from utils.ads1x15 import ADS1115
from utils.micropython_bmpxxx.bmpxxx import BMP390
from utils.logger import log_message
from config.config import I2C_SCL_PIN, I2C_SDA_PIN


class I2CReader:
    def __init__(self, settling_time=1):
        self.settling_time = settling_time
        self.i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        self.adc = ADS1115(self.i2c)
        self.bmp = BMP390(i2c=self.i2c, address=0x77)

    def read(self):
        time.sleep(self.settling_time)
        readings = {}

        try:
            nh3 = self.adc.read(rate=4, channel1=1)
            readings["NH3"] = nh3
        except Exception as e:
            log_message(f"❌ NH3 read error: {e}")

        try:
            h2s = self.adc.read(rate=4, channel1=0)
            readings["H2S"] = h2s
        except Exception as e:
            log_message(f"❌ H2S read error: {e}")

        try:
            readings["Pressure"] = {
                "pressure": self.bmp.pressure,
                "temperature": self.bmp.temperature,
                "altitude": self.bmp.altitude
            }
        except Exception as e:
            log_message(f"❌ BMP390 read error: {e}")

        return readings
