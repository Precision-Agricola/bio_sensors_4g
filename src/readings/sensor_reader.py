"""Reading all sensors wrapper"""
import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay

# All sensors registering
import sensors.amonia.sen0567
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901
#from sensors.pressure.liquid_pressure.sw_p300 import SW_P300

class SensorReader:
    def __init__(self, config_path="config/sensors.json", settling_time=30):
        self.config_path = config_path
        self.sensors = []
        self.sensor_relay = SensorRelay()
        self.settling_time = settling_time
        self.last_readings = {}
        self.load_sensors()
#        self.liquid_pressure_sensor = SW_P300()

    def load_sensors(self):
        """Carga los sensores desde el archivo de configuración"""
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
                        print(f"Registros disponibles: {list(sensor_registry.keys())}")
                except Exception as e:
                    print(f"Error al crear sensor {config.get('name', 'desconocido')}: {str(e)}")
        except Exception as e:
            print(f"Error al cargar sensores: {str(e)}")
    
    def read_sensors(self, relay='A', custom_settling_time=None):
        """
        Lee todos los sensores activando el relé especificado
        
        Args:
            relay: 'A' o 'B' para seleccionar qué grupo de sensores activar
            custom_settling_time: Tiempo personalizado de asentamiento en segundos
        """
        settling = custom_settling_time if custom_settling_time is not None else self.settling_time
        readings = {}
        self.sensor_relay.activate_a()
        time.sleep(settling)
        successful_sensors = []
        for sensor in self.sensors:
            try:
                if not getattr(sensor, '_initialized', True):
                    print(f"Sensor {sensor.name} no está inicializado, omitiendo")
                    continue
                reading = sensor.read()
                if reading is not None:
                    readings[sensor.name] = reading
                    successful_sensors.append(sensor.name)
            except Exception as e:
                print(f"Error al leer sensor {sensor.name}: {str(e)}")
        self.sensor_relay.deactivate_all()

        """
        if hasattr(self, 'liquid_pressure_sensor'):
            try:
                pressure_readings = self.liquid_pressure_sensor.read()
                if pressure_readings:
                    readings[self.liquid_pressure_sensor.name] = pressure_readings
                    successful_sensors.append(self.liquid_pressure_sensor.name)
            except Exception as e:
                with open("sensor_log.txt", "a") as f:
                    f.write(f"{time.time()} ERROR: Error al leer sensor de presión: {str(e)}\n")
        """
        self.last_readings = {
            "timestamp": time.time(),
            "data": readings
        }
        return self.last_readings
    
    def get_last_readings(self):
        """Retorna las últimas lecturas sin leer los sensores nuevamente"""
        return self.last_readings
