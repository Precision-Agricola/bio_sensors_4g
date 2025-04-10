"""Scheduler for sensor readings"""
#src/readings/scheduler.py

import _thread
import time
from readings.sensor_reader import SensorReader
import config.runtime as runtime_config
import gc

class SensorScheduler:
    def __init__(self, settling_time=5):
        self.reader = SensorReader(settling_time=settling_time)
        self.running = False
        self.thread_id = None
        self.last_reading_time = 0
        self.callbacks = []
        
    def start(self):
        """Inicia el hilo que monitorea los aeradores y programa lecturas"""
        if self.running:
            return False
            
        gc.collect()
        self.running = True
        self.thread_id = _thread.start_new_thread(self._monitoring_task, ())
        return True
        
    def stop(self):
        """Detiene el monitoreo y las lecturas programadas"""
        self.running = False
        # En MicroPython no podemos matar hilos directamente
        # Esperamos a que el hilo termine naturalmente
        return True
    
    def add_callback(self, callback):
        """Añade una función callback que se llamará con los resultados de cada lectura"""
        if callable(callback) and callback not in self.callbacks:
            self.callbacks.append(callback)
            return True
        return False
    
    def remove_callback(self, callback):
        """Elimina un callback previamente registrado"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
    
    def _monitoring_task(self):
        """Tarea que corre en un hilo separado para monitorear el ciclo de aeradores"""
        from system.control.relays import LoadRelay
        
        aerator_relay = LoadRelay()
        
        # Inicializar para detectar cambios
        last_state = None
        cycle_start_time = 0
        
        while self.running:
            try:
                # Obtener configuración actual
                time_factor = runtime_config.get_speed()
                on_time = 3 * 3600 // time_factor  # 3 horas en segundos, ajustado por factor
                
                # Obtener estado actual del aerador
                current_state = aerator_relay.get_state()
                
                # Si el estado cambió a encendido, registrar el inicio del ciclo
                if current_state and last_state != current_state:
                    cycle_start_time = time.time()
                    print("Aerador encendido - iniciando ciclo")
                
                # Si el aerador está encendido, verificar si es tiempo de leer sensores
                if current_state:
                    time_elapsed = time.time() - cycle_start_time
                    mid_cycle_time = on_time / 2
                    
                    # Si estamos cerca del punto medio del ciclo y no hemos leído recientemente
                    if (mid_cycle_time - 60) <= time_elapsed <= (mid_cycle_time + 60):
                        # Verificar si ya hicimos una lectura en este ciclo
                        if time.time() - self.last_reading_time > on_time / 2:
                            print(f"Realizando lectura programada a mitad del ciclo (tiempo transcurrido: {time_elapsed}s)")
                            
                            # Leer sensores
                            readings = self.reader.read_sensors(custom_settling_time=10)
                            self.last_reading_time = time.time()
                            
                            # Llamar a callbacks
                            for callback in self.callbacks:
                                try:
                                    callback(readings)
                                except Exception as e:
                                    print(f"Error en callback: {e}")
                
                # Actualizar último estado conocido
                last_state = current_state
                
                # Esperar antes de la siguiente verificación
                time.sleep(30)  # Verificar cada 30 segundos es suficiente
                
            except Exception as e:
                print(f"Error en tarea de monitoreo: {e}")
                time.sleep(60)  # Esperar más tiempo si hay error
    
    def read_now(self):
        """Realiza una lectura inmediata sin esperar al ciclo"""
        readings = self.reader.read_sensors()
        
        # Llamar a los callbacks registrados
        for callback in self.callbacks:
            try:
                callback(readings)
            except Exception as e:
                print(f"Error en callback: {e}")
                
        return readings
