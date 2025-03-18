# src/routines/sensor_routine.py
from readings.scheduler import SensorScheduler
from local_network.http_client import HTTPClient  # Only HTTP client import
from local_network.wifi import connect_wifi
import ujson as json
import gc
import os

class SensorRoutine:
    def __init__(self, data_folder="data"):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.http_client = HTTPClient()  # Initialize HTTP client
        
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
        
    def start(self):
        print("Iniciando rutina de lecturas de sensores...")
        success = self.scheduler.start()
        return success
    
    def stop(self):
        print("Deteniendo rutina de lecturas de sensores...")
        return self.scheduler.stop()
    
    def read_now(self):
        print("Realizando lectura inmediata de sensores...")
        return self.scheduler.read_now()
    
    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            print("No hay datos para guardar")
            return
            
        try:
            timestamp = readings['timestamp']
            filename = f"{self.data_folder}/sensors_{int(timestamp)}.json"
            
            with open(filename, 'w') as f:
                json.dump(readings, f)
            
            print(f"Datos guardados en {filename}")
            
            # Send data via HTTP
            try:
                if self.http_client.send_data(readings):
                    print("Datos enviados por HTTP correctamente")
                else:
                    print("Error al enviar datos por HTTP")
            except Exception as e:
                print(f"Error HTTP: {e}")
            
            gc.collect()
            
        except Exception as e:
            print(f"Error al guardar datos: {e}")
    
    def check_commands(self):
        """
        Check for commands from the server
        This can be expanded in the future to poll HTTP endpoints for commands
        """
        try:
            if not connect_wifi():
                return False
            return False
        except Exception as e:
            print(f"Error checking commands: {e}")
            return False
