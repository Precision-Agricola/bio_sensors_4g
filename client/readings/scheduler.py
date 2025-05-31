# client/readings/scheduler.py

import _thread
import time
import gc
import machine
from readings.sensor_reader import SensorReader
from config import runtime as runtime_config
from utils.logger import log_message

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
        try:
            from system.control.relays import LoadRelay
            relay = LoadRelay()
        except Exception as e:
            log_message(f"ERROR LoadRelay: {e}")
            self.running = False
            return

        log_message("Tarea monitoreo iniciada (3 lecturas ON / 3 OFF).")

        last_state = relay.get_state(idx=0)
        now = time.time()
        time_factor = max(1, runtime_config.get_speed())

        on_time = 3 * 3600 // time_factor
        off_time = 3 * 3600 // time_factor
        on_interval = on_time / 3.0
        off_interval = off_time / 3.0

        on_start, off_start = now, now
        on_target, off_target = now + on_interval, now + off_interval
        on_count, off_count = 0, 0

        if last_state:
            on_start = now
            on_target = on_start + on_interval
        else:
            off_start = now
            off_target = off_start + off_interval

        while self.running:
            try:
                state = relay.get_state(idx=0)
                now = time.time()

                if state != last_state:
                    try:
                        time_factor = max(1, runtime_config.get_speed())
                        on_time = 3 * 3600 // time_factor
                        off_time = 3 * 3600 // time_factor
                        on_interval = on_time / 3.0
                        off_interval = off_time / 3.0
                    except:
                        pass

                    if state:
                        on_start = now
                        on_target = on_start + on_interval
                        on_count = 0
                    else:
                        off_start = now
                        off_target = off_start + off_interval
                        off_count = 0

                should_read = False

                if state and on_count < 3 and now >= on_target:
                    should_read = True
                    on_count += 1
                    if on_count < 3:
                        on_target = on_start + (on_count + 1) * on_interval

                elif not state and off_count < 3 and now >= off_target:
                    should_read = True
                    off_count += 1
                    if off_count < 3:
                        off_target = off_start + (off_count + 1) * off_interval

                if should_read:
                    try:
                        readings = self.reader.read_sensors(aerator_state=state)
                        self.last_reading_time = now
                        for cb in self.callbacks:
                            cb(readings)
                        gc.collect()
                    except Exception as e:
                        log_message(f"ERROR read/callback: {e}")

                last_state = state
                time.sleep(10)

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
