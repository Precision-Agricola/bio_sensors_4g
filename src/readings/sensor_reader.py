# readings/sensor_reader.py
import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay

import sensors.amonia.sen0567
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901

class SensorReader:
    def __init__(self, config_path="config/sensors.json", settling_time=30):
        self.config_path = config_path
        self.sensors = []
        self.sensor_relay = SensorRelay()
        self.settling_time = settling_time
        self.last_readings = {}
        self.load_sensors()
    
    def load_sensors(self):
        """Carga los sensores desde el archivo de configuración"""
        try:
            with open(self.config_path, 'r') as f:
                sensor_configs = json.load(f)
            
            self.sensors = []
            
            for config in sensor_configs:
                model = config["model"].upper()
                protocol = config["protocol"].upper()
                key = (model, protocol)
                
                if key in sensor_registry:
                    sensor_class = sensor_registry[key]
                    sensor = sensor_class(**config)
                    self.sensors.append(sensor)
                    print(f"Sensor cargado: {config['name']}")
                else:
                    print(f"Sensor no encontrado: {model}, {protocol}")
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
        
        if relay == 'A':
            self.sensor_relay.activate_a()
        elif relay == 'B':
            self.sensor_relay.activate_b()
        else:
            print(f"Relé '{relay}' no válido")
            return {}
        
        print(f"Esperando tiempo de asentamiento ({settling}s)...")
        time.sleep(settling)
        
        for sensor in self.sensors:
            try:
                reading = sensor.read()
                if reading is not None:
                    readings[sensor.name] = reading
            except Exception as e:
                print(f"Error al leer sensor {sensor.name}: {str(e)}")
        
        self.sensor_relay.deactivate_all()
        
        self.last_readings = {
            "timestamp": time.time(),
            "data": readings
        }
        return self.last_readings
    
    def get_last_readings(self):
        """Retorna las últimas lecturas sin leer los sensores nuevamente"""
        return self.last_readings
