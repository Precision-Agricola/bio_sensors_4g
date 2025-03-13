"""Sensor routine monitoring the aerator timer"""

# routines/sensor_routine.py
"""
Sensor reading routine module for BIO-IOT system
Precision Agrícola - Investigation and Development Department
March 2025
"""
from readings.scheduler import SensorScheduler
import ujson as json
import gc
import os

class SensorRoutine:
    def __init__(self, data_folder="data"):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)
    
    def start(self):
        """Inicia la rutina de lectura de sensores"""
        print("Iniciando rutina de lecturas de sensores...")
        return self.scheduler.start()
    
    def stop(self):
        """Detiene la rutina de lectura de sensores"""
        print("Deteniendo rutina de lecturas de sensores...")
        return self.scheduler.stop()
    
    def read_now(self):
        """Realiza una lectura inmediata"""
        print("Realizando lectura inmediata de sensores...")
        return self.scheduler.read_now()
    
    def _save_data_callback(self, readings):
        """Callback para guardar datos en archivo"""
        if not readings or 'data' not in readings:
            print("No hay datos para guardar")
            return
            
        try:
            timestamp = readings['timestamp']
            filename = f"{self.data_folder}/sensors_{int(timestamp)}.json"
            
            with open(filename, 'w') as f:
                json.dump(readings, f)
            
            print(f"Datos guardados en {filename}")
            
            gc.collect()
            
        except Exception as e:
            print(f"Error al guardar datos: {e}")
