import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay
from utils.logger import log_message


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
        
        self.last_readings = {
            "timestamp": time.time(),
            "data": readings
        }
        return self.last_readings
    
    def get_last_readings(self):
        return self.last_readings
