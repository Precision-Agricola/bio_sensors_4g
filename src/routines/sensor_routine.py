# routines/sensor_routine.py
from readings.scheduler import SensorScheduler
from local_network.mqtt import MQTTManager
from local_network.wifi import connect_wifi
import ujson as json
import gc
import os

class SensorRoutine:
    def __init__(self, data_folder="data"):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.mqtt = MQTTManager()
        
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
        self.mqtt.register_command_handler("READ_NOW", self._handle_read_now)
        
    def start(self):
        print("Iniciando rutina de lecturas de sensores...")
        success = self.scheduler.start()
        
        if success:
            if connect_wifi():
                self.mqtt.start_command_listener()
                print("Escucha de comandos MQTT iniciada")
        
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
                print("WiFi conectado, enviando datos por MQTT")
                if self.mqtt.publish(readings):
                    print("Datos enviados por MQTT correctamente")
                else:
                    print("Error al enviar datos por MQTT")
            
            gc.collect()
            
        except Exception as e:
            print(f"Error al guardar datos: {e}")
    
    def _handle_read_now(self, params):
        print("Comando READ_NOW recibido, realizando lectura inmediata")
        return self.read_now()
    
    def check_commands(self):
        if connect_wifi():
            return self.mqtt.check_commands()
        return False
