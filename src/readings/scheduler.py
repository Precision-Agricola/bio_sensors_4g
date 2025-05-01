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
        log_message("Tarea monitoreo iniciada (3 lecturas ON / 3 OFF).")
        try:
            from system.control.relays import LoadRelay
            aerator_relay = LoadRelay()
        except Exception as e:
            log_message(f"Error CRITICO LoadRelay: {e}"); self.running = False; return

        last_state = aerator_relay.get_state()
        on_cycle_start_time = 0
        off_cycle_start_time = 0
        on_read_count = 0
        off_read_count = 0
        # Defaults iniciales y cálculo de intervalos
        on_time = 3*3600; off_time = 3*3600; time_factor = 1
        try: time_factor = runtime_config.get_speed() # Intentar leer config
        except: pass
        on_time = max(1, 3*3600 // time_factor); off_time = max(1, 3*3600 // time_factor)
        on_read_interval = on_time / 3.0; off_read_interval = off_time / 3.0
        next_on_read_target = 0; next_off_read_target = 0

        # Establecer estado inicial
        now = time.time()
        if last_state:
            on_cycle_start_time = now
            next_on_read_target = on_cycle_start_time + on_read_interval
        else:
            off_cycle_start_time = now
            next_off_read_target = off_cycle_start_time + off_read_interval

        while self.running:
            try:
                #TODO: aerator state always is shown as "ON", inspect why state "OFF" is not correctly read
                current_state = aerator_relay.get_state()
                state_changed = (current_state != last_state)
                now = time.time()

                if state_changed:
                    # Recalcular tiempos y reiniciar contadores al cambiar estado
                    try: # Actualizar tiempos desde config
                        time_factor=runtime_config.get_speed()
                        on_time=max(1, 3*3600 // time_factor); off_time=max(1, 3*3600 // time_factor)
                        on_read_interval=on_time / 3.0; off_read_interval=off_time / 3.0
                    except: pass # Usar valores previos si falla config

                    if current_state: # A -> ON
                        on_cycle_start_time = now; on_read_count = 0
                        next_on_read_target = on_cycle_start_time + on_read_interval
                    else: # A -> OFF
                        off_cycle_start_time = now; off_read_count = 0
                        next_off_read_target = off_cycle_start_time + off_read_interval

                # Reboot check (sin cambios)
                if state_changed and runtime_config.is_reboot_requested():
                    log_message("!!! Rebooting..."); time.sleep(3); machine.reset()

                # --- Lógica de Lectura (3 ON / 3 OFF) ---
                common_read_args = {'custom_settling_time': 10, 'aerator_state': current_state}

                # Lecturas durante ciclo ON
                if current_state and on_read_count < 3 and now >= next_on_read_target:
                    log_message(f"INFO: Lectura ON {on_read_count + 1}/3...")
                    try:
                        readings = self.reader.read_sensors(**common_read_args)
                        self.last_reading_time = now
                        for callback in self.callbacks: callback(readings)
                        gc.collect()
                    except Exception as e: log_message(f"ERROR ON read/callback: {e}")
                    on_read_count += 1
                    if on_read_count < 3: # Calcular siguiente si aún faltan
                        next_on_read_target = on_cycle_start_time + (on_read_count + 1) * on_read_interval

                # Lecturas durante ciclo OFF
                elif not current_state and off_read_count < 3 and now >= next_off_read_target:
                    log_message(f"INFO: Lectura OFF {off_read_count + 1}/3...")
                    try:
                        readings = self.reader.read_sensors(**common_read_args)
                        self.last_reading_time = now
                        for callback in self.callbacks: callback(readings)
                        gc.collect()
                    except Exception as e: log_message(f"ERROR OFF read/callback: {e}")
                    off_read_count += 1
                    if off_read_count < 3: # Calcular siguiente si aún faltan
                        next_off_read_target = off_cycle_start_time + (off_read_count + 1) * off_read_interval
                # --- Fin Lógica de Lectura ---

                last_state = current_state
                time.sleep(10) # Pausa del bucle principal

            except Exception as e:
                log_message(f"Error grave en _monitoring_task: {e}")
                time.sleep(60) # Pausa larga en caso de error grave

        log_message("Tarea de monitoreo finalizada.")

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
