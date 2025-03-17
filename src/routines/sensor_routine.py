# routines/sensor_routine.py
from readings.scheduler import SensorScheduler
from local_network.wifi import connect_wifi
from local_network.http_client import HTTPClient
import ujson as json
import gc
import os

class SensorRoutine:
    def __init__(self, data_folder="data", device_id = 'esp32-01'):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.http = HTTPClient()
        self.device_id= device_id
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
        
    def start(self):
        print("Starting sensor reading routine")
        success = self.scheduler.start()

        if success:
            connect_wifi()
            print('HTTP communication ready')

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
            
            if connect_wifi():
                print("WiFi connected, sending data via HTTP")
                if self.http.send_sensor_data(readings): 
                    print("Data sent via HTTP successfully")
                else:
                    print("Failed to send via HTTP")
            
            gc.collect()
            
        except Exception as e:
            print(f"Error al guardar datos: {e}")
    
    def _handle_read_now(self, params):
        print("Comando READ_NOW recibido, realizando lectura inmediata")
        return self.read_now()
    
    def check_commands(self):
        if connect_wifi():
            commands = self.http.check_commands(self.device_id)
            for cmd in commands:
                self._handle_command(cmd)
            return bool(commands)
        return False
    
    def _handle_command(self, command):
        if command == 'READ_NOW':
            print("HTTP command received: READ_NOW")
            self.read_now()