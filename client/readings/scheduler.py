# client/readings/scheduler.py

import _thread
import time
import gc
from readings.sensor_reader import SensorReader
from config import runtime as runtime_config
from utils.logger import log_message
from system.control.aerator_controller import aerator

class SensorScheduler:
    def __init__(self):
        self.reader = SensorReader()
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
        log_message("Tarea monitoreo lógica (3 lecturas por fase, sin espacios muertos).")

        while self.running:
            try:
                state = aerator.get_logical_state()

                time_factor = max(1, runtime_config.get_speed())
                cycle_hours = runtime_config.get_cycle_duration()
                duty_cycle = runtime_config.get_duty_cycle()
                readings_per_phase = 3

                if state:
                    total_seconds = int(cycle_hours * 3600 * duty_cycle) // time_factor
                else:
                    total_seconds = int(cycle_hours * 3600 * (1 - duty_cycle)) // time_factor

                interval = total_seconds // readings_per_phase

                log_message(f"Fase lógica: {'ON' if state else 'OFF'} | Intervalo: {interval}s")

                for _ in range(readings_per_phase):
                    if not self.running:
                        return

                    try:
                        readings = self.reader.read_sensors(aerator_state=state)
                        self.last_reading_time = time.time()
                        for cb in self.callbacks:
                            cb(readings)
                        gc.collect()
                    except Exception as e:
                        log_message(f"ERROR read/callback: {e}")

                    time.sleep(interval)

            except Exception as e:
                log_message(f"ERROR grave monitoreo: {e}")
                time.sleep(60)

        log_message("Tarea de monitoreo finalizada.")

    def read_now(self):
        log_message("Lectura inmediata solicitada")
        try:
            readings = self.reader.read_sensors()
            self.last_reading_time = time.time()
            for cb in self.callbacks:
                cb(readings)
            gc.collect()
            return readings
        except Exception as e:
            log_message(f"Error en lectura inmediata: {e}")
            return {}
