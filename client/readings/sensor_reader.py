from readings.i2c_readings import read_i2c_sensors
from readings.analog_readings import read_analog_sensors
from readings.rs485_readings import read_rs485_sensors
from calendar.rtc_utils import get_timestamp
from utils.logger import log_message

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

        timestamp = get_timestamp()
        self.last_readings = {
            "timestamp": timestamp,
            "data": data
        }

        if aerator_state is not None:
            self.last_readings["aerator_status"] = "ON" if aerator_state else "OFF"

        return self.last_readings
