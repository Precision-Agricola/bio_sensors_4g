import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay
from utils.logger import log_message

from calendar.rtc_manager import RTCManager
import sensors.amonia.sen0567
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901
import sensors.ph.ph_sensor
import sensors.rs485.rs485_sensor


class SensorReader:
    def __init__(self, config_path="config/sensors.json", settling_time=30):
        self.config_path = config_path
        self.sensors = []
        self.sensor_relay = SensorRelay()
        self.settling_time = settling_time
        self.last_readings = {}
        self.rtc_manager = self._init_rtc_manager()
        self.load_sensors()

    def _init_rtc_manager(self):
        try:
            rtc = RTCManager()
            if not (rtc and rtc.rtc):
                log_message("WARN:", "RTCManager hardware init fallido.")
                return None
            return rtc
        except Exception as e:
            log_message("ERROR:", "RTCManager init:", e)
            return None

    def load_sensors(self):
        try:
            with open(self.config_path, 'r') as f:
                sensor_configs = json.load(f)
        except Exception as e:
            log_message("ERROR:", f"No se pudo cargar '{self.config_path}':", e)
            return

        for config in sensor_configs:
            try:
                key = (config["model"].upper(), config["protocol"].upper())
                sensor_class = sensor_registry.get(key)
                if not sensor_class:
                    log_message("WARN:", f"Sensor no registrado: {key}")
                    continue
                sensor = sensor_class(**config)
                self.sensors.append(sensor)
            except KeyError as e:
                log_message("ERROR:", f"Falta clave {e} en config: {config.get('name', 'desconocido')}")
            except Exception as e:
                log_message("ERROR:", f"Creando sensor {config.get('name', 'desconocido')}: {e}")

    def read_sensors(self, relay='A', custom_settling_time=None, aerator_state=None):
        settling = custom_settling_time if custom_settling_time is not None else self.settling_time
        readings = {}
        successful_sensors = []

        try:
            self.sensor_relay.activate_a()
            time.sleep(settling)

            for sensor in self.sensors:
                if not getattr(sensor, '_initialized', True):
                    continue
                try:
                    result = sensor.read()
                    if result is not None:
                        readings[getattr(sensor, 'name', 'desconocido')] = result
                        successful_sensors.append(sensor)
                except Exception as e:
                    log_message("ERROR:", f"Lectura fallida: {sensor.name}", e)
        except Exception as e:
            log_message("ERROR:", "Fallo en activación o lectura de sensores:", e)
        finally:
            try:
                self.sensor_relay.deactivate_all()
            except Exception as e:
                log_message("ERROR:", "Fallo desactivando relays:", e)

        timestamp = self._get_timestamp()
        self.last_readings = {"timestamp": timestamp, "data": readings}
        if aerator_state is not None:
            self.last_readings['aerator_status'] = "ON" if aerator_state else "OFF"
        log_message("INFO:", f"Lectura completada ({len(successful_sensors)} sensores). Timestamp: {timestamp}")
        return self.last_readings

    def _get_timestamp(self):
        if self.rtc_manager:
            try:
                t = self.rtc_manager.get_time_tuple()
                if t:
                    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*t[:6])
                return "RTC_READ_ERROR"
            except Exception as e:
                log_message("ERROR:", "RTCManager timestamp error:", e)
                return "RTC_EXCEPTION"
        return "RTC_UNAVAILABLE"

    def get_last_readings(self):
        return self.last_readings
