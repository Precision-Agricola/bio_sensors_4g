# client/readings/sensor_reader.py

from readings.i2c_readings import read_i2c_sensors
from readings.analog_readings import read_analog_sensors
from readings.rs485_readings import read_rs485_sensors
from calendar.rtc_utils import get_fallback_timestamp
from utils.logger import log_message
from system.control.aerator_controller import aerator

class SensorReader:
    def __init__(self):
        self.last_readings = {}

    def read_sensors(self, aerator_state=None):
        data = {}

        def flatten(sensor_data):
            for key, value in sensor_data.items():
                if isinstance(value, dict):
                    data.update(value)
                else:
                    data[key] = value

        # --- I2C ---
        try:
            flatten(read_i2c_sensors())
        except Exception as e:
            log_message("Error en lectura I2C", e)

        # --- Analógicos ---
        try:
            flatten(read_analog_sensors())
        except Exception as e:
            log_message("Error en lectura analógica", e)

        # --- RS485 ---
        try:
            flatten(read_rs485_sensors())
        except Exception as e:
            log_message("Error en lectura RS485", e)

        timestamp = get_fallback_timestamp() # Fallback timestamp if RTC is unavailable
        self.last_readings = {
            "timestamp": timestamp,
            "data": data
        }

        if aerator_state is None:
            aerator_state = aerator.get_logical_state()
        
        self.last_readings["aerators"] = aerator.get_logical_states()

        return self.last_readings
