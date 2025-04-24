import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay
from utils.logger import log_message

try:
    from calendar.get_time import init_rtc as initialize_external_rtc
    from calendar.get_time import get_current_time as read_external_rtc
except ImportError:
    log_message("ERROR: No se pudieron importar funciones RTC desde calendar.get_time")
    def initialize_external_rtc(): return None
    def read_external_rtc(rtc_obj): return None

# All sensors registering
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
        self.rtc_device = None
        try:
            if initialize_external_rtc:
                self.rtc_device = initialize_external_rtc()
                if self.rtc_device:
                    log_message("Objeto RTC DS1302 inicializado en SensorReader.")
                else:
                    log_message("Fallo al inicializar objeto RTC DS1302 en SensorReader.")
        except Exception as e:
            log_message(f"Excepción al inicializar RTC DS1302 en SensorReader: {e}")
        self.load_sensors()
    
    def load_sensors(self):
        try:
            with open(self.config_path, 'r') as f:
                sensor_configs = json.load(f)
            
            self.sensors = []
            
            for config in sensor_configs:
                try:
                    model = config["model"].upper()
                    protocol = config["protocol"].upper()
                    key = (model, protocol)
                    
                    if key in sensor_registry:
                        sensor_class = sensor_registry[key]
                        sensor = sensor_class(**config)
                        self.sensors.append(sensor)
                    else:
                        log_message(f"Registros disponibles: {list(sensor_registry.keys())}")
                except Exception as e:
                    log_message(f"Error al crear sensor {config.get('name', 'desconocido')}: {str(e)}")
        except Exception as e:
            log_message(f"Error al cargar sensores: {str(e)}")
    
    def read_sensors(self, relay='A', custom_settling_time=None):
        settling = custom_settling_time if custom_settling_time is not None else self.settling_time
        readings = {}
        self.sensor_relay.activate_a()
        time.sleep(settling)
        successful_sensors = []
        for sensor in self.sensors:
            try:
                if not getattr(sensor, '_initialized', True):
                    log_message(f"Sensor {sensor.name} no está inicializado, omitiendo")
                    continue
                reading = sensor.read()
                if reading is not None:
                    readings[sensor.name] = reading
                    successful_sensors.append(sensor.name)
            except Exception as e:
                log_message(f"Error al leer sensor {sensor.name}: {str(e)}")
        self.sensor_relay.deactivate_all()
        timestamp_iso = "RTC_READ_ERROR" # Valor por defecto en caso de error
        try:
            if self.rtc_device and read_external_rtc:
                now_tuple_ext = read_external_rtc(self.rtc_device)
                if now_tuple_ext:
                     timestamp_iso = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(now_tuple_ext[0], now_tuple_ext[1], now_tuple_ext[2], now_tuple_ext[3], now_tuple_ext[4], now_tuple_ext[5])
                else:
                     log_message("Error: read_external_rtc devolvió None.")
            else:
                 log_message("Error: Objeto RTC DS1302 no disponible para leer timestamp.")
        except Exception as e:
            log_message(f"Error al obtener/formatear timestamp desde DS1302: {e}") 
        self.last_readings = {
            "timestamp":timestamp_iso, 
            "data": readings
        }
        return self.last_readings
    
    def get_last_readings(self):
        return self.last_readings
