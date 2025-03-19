"""Reading all sensors wrapper"""
import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay

# All sensors registering
import sensors.amonia.sen0567
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901
import sensors.pressure.liquid_pressure.sw_p300

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
        # Activar el relé apropiado
        if relay == 'A':
            self.sensor_relay.activate_a()
        elif relay == 'B':
            self.sensor_relay.activate_b()
        
        time.sleep(settling)
        successful_sensors = []
        
        # Registrar inicio de lectura
        try:
            with open('sensor_debug.txt', 'a') as f:
                f.write(f"\n[{time.time()}] Iniciando lectura de sensores (relay: {relay})\n")
        except:
            pass
        
        # Primero verificar si hay sensores RS485 para un seguimiento especial
        rs485_sensors = []
        for sensor in self.sensors:
            if getattr(sensor, 'protocol', '').upper() == 'RS485':
                rs485_sensors.append(sensor)
        
        # Registrar cuántos sensores RS485 encontramos
        try:
            with open('sensor_debug.txt', 'a') as f:
                f.write(f"[{time.time()}] Sensores RS485 encontrados: {len(rs485_sensors)}\n")
                for s in rs485_sensors:
                    f.write(f"  - {s.name} (modelo: {s.model})\n")
        except:
            pass
        
        # Leer todos los sensores
        for sensor in self.sensors:
            try:
                # Registrar inicio de lectura del sensor
                try:
                    with open('sensor_debug.txt', 'a') as f:
                        f.write(f"[{time.time()}] Intentando leer sensor: {sensor.name}\n")
                except:
                    pass
                
                if not getattr(sensor, '_initialized', True):
                    try:
                        with open('sensor_debug.txt', 'a') as f:
                            f.write(f"[{time.time()}] Sensor {sensor.name} no inicializado, omitiendo\n")
                    except:
                        pass
                    continue
                
                # Seguimiento especial para sensores RS485
                is_rs485 = getattr(sensor, 'protocol', '').upper() == 'RS485'
                
                # Leer el sensor
                reading = sensor.read()
                
                # Registrar resultado de lectura
                if reading is not None:
                    readings[sensor.name] = reading
                    successful_sensors.append(sensor.name)
                    
                    # Registro especial para RS485
                    if is_rs485:
                        try:
                            with open('sensor_debug.txt', 'a') as f:
                                f.write(f"[{time.time()}] ✅ Lectura RS485 exitosa: {sensor.name}\n")
                                f.write(f"    Datos: {reading}\n")
                                
                                # Verificar condiciones específicas de temperatura
                                if 'temperature' in reading:
                                    temp = reading['temperature']
                                    if 18 <= temp <= 30:
                                        f.write(f"    ESTADO: Temperatura normal ({temp}°C)\n")
                                    else:
                                        f.write(f"    ALERTA: Temperatura fuera de rango ({temp}°C)\n")
                        except:
                            pass
                else:
                    # Registro especial para fallo de RS485
                    if is_rs485:
                        try:
                            with open('sensor_debug.txt', 'a') as f:
                                f.write(f"[{time.time()}] ❌ Fallo en lectura RS485: {sensor.name}\n")
                        except:
                            pass
                            
            except Exception as e:
                # Registrar excepción
                try:
                    with open('sensor_debug.txt', 'a') as f:
                        f.write(f"[{time.time()}] ❌ Error leyendo sensor {sensor.name}: {str(e)}\n")
                except:
                    pass
                    
        # Desactivar todos los relés
        self.sensor_relay.deactivate_all()
        
        # Registrar resumen
        try:
            with open('sensor_debug.txt', 'a') as f:
                f.write(f"[{time.time()}] Finalizada lectura de sensores\n")
                f.write(f"  - Sensores exitosos: {len(successful_sensors)} de {len(self.sensors)}\n")
                f.write(f"  - Nombres: {', '.join(successful_sensors)}\n\n")
        except:
            pass
        
        self.last_readings = {
            "timestamp": time.time(),
            "data": readings
        }
        return self.last_readings
    
    def get_last_readings(self):
        """Retorna las últimas lecturas sin leer los sensores nuevamente"""
        return self.last_readings
