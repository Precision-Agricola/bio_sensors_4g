#src/readings/scheduler.py
import _thread
import time
from readings.sensor_reader import SensorReader
import config.runtime as runtime_config
import gc
import machine
from utils.logger import log_message


class SensorScheduler:
    def __init__(self, settling_time=5):
        self.reader = SensorReader(settling_time=settling_time)
        self.running = False
        self.thread_id = None
        self.last_reading_time = 0
        self.callbacks = []
        
    def start(self):
        if self.running:
            return False

        gc.collect()
        self.running = True
        self.thread_id = _thread.start_new_thread(self._monitoring_task, ())
        return True
        
    def stop(self):
        self.running = False
        # En MicroPython no podemos matar hilos directamente
        # Esperamos a que el hilo termine naturalmente
        return True
    
    def add_callback(self, callback):
        if callable(callback) and callback not in self.callbacks:
            self.callbacks.append(callback)
            return True
        return False
    
    def remove_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
    
    def _monitoring_task(self):
        log_message("Tarea de monitoreo de sensores iniciada.")
        try:
            from system.control.relays import LoadRelay
            aerator_relay = LoadRelay()
            log_message("Instancia de LoadRelay creada en _monitoring_task.")
        except Exception as e:
            log_message(f"Error CRÍTICO al importar/instanciar LoadRelay: {e}")
            log_message("La tarea de monitoreo no puede continuar sin control de relés.")
            self.running = False
            return

        last_state = aerator_relay.get_state()
        log_message(f"Estado inicial del aireador: {'ON' if last_state else 'OFF'}")
        cycle_start_time = time.time() if last_state else 0

        while self.running:
            try:
                current_state = aerator_relay.get_state()
                state_changed = (current_state != last_state)

                if state_changed:
                    log_message(f"Cambio de estado del aireador detectado: {'OFF' if last_state else 'ON'} -> {'ON' if current_state else 'OFF'}")
                    if current_state:
                        cycle_start_time = time.time()

                if state_changed and runtime_config.is_reboot_requested():
                    log_message("!!! Condición de reinicio cumplida: Cambio de estado del ciclo y bandera activa.")
                    log_message("!!! Reiniciando el sistema en 3 segundos...")
                    time.sleep(3)
                    machine.reset()

                if current_state:
                    time_factor = runtime_config.get_speed()
                    on_time = 3 * 3600 // time_factor
                    time_elapsed = time.time() - cycle_start_time
                    mid_cycle_time = on_time / 2

                    read_window_start = mid_cycle_time - 120 
                    read_window_end = mid_cycle_time + 120
                    min_time_since_last_read = on_time / 3

                    if read_window_start <= time_elapsed <= read_window_end and \
                       (time.time() - self.last_reading_time > min_time_since_last_read):

                        log_message(f"Punto medio del ciclo ON alcanzado (t={int(time_elapsed)}s). Realizando lectura de sensores...")
                        readings = self.reader.read_sensors(custom_settling_time=10)
                        self.last_reading_time = time.time()
                        log_message(f"Lectura completada: {readings}")

                        for callback in self.callbacks:
                            try:
                                callback(readings)
                            except Exception as e:
                                log_message(f"Error en callback del scheduler: {e}")
                        gc.collect()

                last_state = current_state
                time.sleep(10)

            except Exception as e:
                log_message(f"Error grave en _monitoring_task: {e}")
                time.sleep(60)

        log_message("Tarea de monitoreo de sensores finalizada.")

    def read_now(self):
        log_message("Realizando lectura inmediata de sensores...")
        readings = self.reader.read_sensors()
        log_message(f"Lectura inmediata: {readings}")
        for callback in self.callbacks:
            try:
                callback(readings)
            except Exception as e:
                log_message(f"Error en callback (read_now): {e}")
        gc.collect()
        return readings
