import json
import time
from sensors.base import sensor_registry
from system.control.relays import SensorRelay
from utils.logger import log_message

try:
    from calendar.rtc_manager import RTCManager
    _RTC_MANAGER_AVAILABLE = True
except ImportError as e:
    log_message("ERROR:", "Import RTCManager fallido:", e)
    RTCManager = None
    _RTC_MANAGER_AVAILABLE = False

# --- Importar Clases de Sensores (para registro) ---
# Esto asegura que las clases se añadan al sensor_registry
try:
    import sensors.amonia.sen0567
    import sensors.hydrogen_sulfide.sen0568
    import sensors.pressure.bmp3901
    import sensors.ph.ph_sensor
    import sensors.rs485.rs485_sensor
except ImportError as e:
    log_message("WARN:", "Fallo al importar uno o más módulos de sensor:", e)

# --- Clase Principal ---
class SensorReader:
    def __init__(self, config_path="config/sensors.json", settling_time=30):
        self.config_path = config_path
        self.sensors = []
        self.sensor_relay = SensorRelay() # Asume que esta clase funciona
        self.settling_time = settling_time
        self.last_readings = {}
        self.rtc_manager = None

        # Inicializar RTCManager
        if _RTC_MANAGER_AVAILABLE:
            try:
                self.rtc_manager = RTCManager()
                # Chequeo adicional si el hardware interno del manager inicializó bien
                if not (self.rtc_manager and self.rtc_manager.rtc):
                     log_message("WARN:", "SensorReader: RTCManager hardware init fallido.")
                     self.rtc_manager = None
            except Exception as e:
                 log_message("ERROR:", "SensorReader: Creando RTCManager:", e)
                 self.rtc_manager = None
        # else: log_message("INFO:", "SensorReader: RTCManager no disponible.") # Log opcional

        self.load_sensors()

    def load_sensors(self):
        # Carga la configuración de sensores desde JSON
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
                        log_message("WARN:", "Sensor no encontrado en registro:", key)
                except KeyError as e:
                     log_message("ERROR:", f"Falta clave {e} en config sensor:", config.get('name', 'desconocido'))
                except Exception as e:
                    log_message("ERROR:", f"Creando sensor {config.get('name', 'desconocido')}:", e)
        except OSError as e:
             log_message("ERROR:", f"No se pudo abrir/leer '{self.config_path}':", e)
        except Exception as e:
            log_message("ERROR:", f"Cargando config sensores:", e)

    def read_sensors(self, relay='A', custom_settling_time=None):
        # Activa relay, espera, lee sensores, desactiva relay y obtiene timestamp
        settling = custom_settling_time if custom_settling_time is not None else self.settling_time
        readings = {}
        successful_sensors = []

        try:
            self.sensor_relay.activate_a() # Asume activación de relay A
            time.sleep(settling)

            for sensor in self.sensors:
                sensor_name = getattr(sensor, 'name', 'desconocido')
                try:
                    if not getattr(sensor, '_initialized', True):
                        continue # Omitir si no está inicializado
                    reading = sensor.read()
                    if reading is not None:
                        readings[sensor_name] = reading
                        successful_sensors.append(sensor_name)
                except Exception as e:
                    log_message(f"Error:", "Leyendo sensor", sensor_name, ":", e)

        except Exception as e:
             log_message("ERROR:", "Durante activación/lectura sensores:", e)
        finally:
             # Asegura desactivación del relay
             try:
                 self.sensor_relay.deactivate_all()
             except Exception as e:
                 log_message("ERROR:", "Desactivando relay:", e)

        # Obtener timestamp usando el RTCManager
        timestamp_iso = "RTC_UNAVAILABLE" # Default
        if self.rtc_manager:
            try:
                now_tuple = self.rtc_manager.get_time_tuple() # Usa el manager
                if now_tuple:
                    # Formato YYYY-MM-DDTHH:MM:SS
                    timestamp_iso = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*now_tuple[:6])
                else:
                    timestamp_iso = "RTC_READ_ERROR" # Error al leer tupla
            except Exception as e:
                 log_message("ERROR:", "Obteniendo timestamp RTCManager:", e)
                 timestamp_iso = "RTC_EXCEPTION"
        # else: Opcional: Añadir fallback a RTC interno aquí

        log_message("INFO:", f"Lectura completada. OK:", len(successful_sensors), "Timestamp:", timestamp_iso)
        self.last_readings = {
            "timestamp": timestamp_iso,
            "data": readings
        }
        return self.last_readings

    def get_last_readings(self):
        return self.last_readings
