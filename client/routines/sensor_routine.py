import ujson as json
import gc
import os
import time
from readings.scheduler import SensorScheduler
from config.secrets import DEVICE_ID
from utils.logger import log_message
from machine import UART

class SensorRoutine:
    def __init__(self, data_folder="data", device_id=DEVICE_ID):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.device_id = device_id
        self._retry_flag = False

        try:
            os.mkdir(data_folder)
        except OSError:
            pass

        self.scheduler.add_callback(self._save_data_callback)

    def mark_retry_flag(self): self._retry_flag = True
    def should_retry(self): return self._retry_flag

    def retry_pending_data_if_needed(self):
        if self._retry_flag:
            log_message("Retrying to send pending data...")
            self.retry_pending_data()
            self._retry_flag = False

    def start(self):
        log_message("Starting sensor routine...")
        return self.scheduler.start()

    def stop(self):
        log_message("Stopping sensor routine...")
        return self.scheduler.stop()

    def read_now(self):
        log_message("Performing immediate sensor reading...")
        return self.scheduler.read_now()

    def _send_via_uart(self, readings):
        try:
            readings["device_id"] = self.device_id
            uart = UART(1, tx=0, rx=2, baudrate=9600)
            uart.write(json.dumps(readings) + "\n")

            print("UART data sent:", readings)
            log_message("Data sent via UART")
            return True
        except Exception as e:
            log_message(f"UART send failed: {e}")
            return False

    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            log_message("No data to save")
            return

        try:
            ts = readings['timestamp'].replace(':', '-').replace('T', '_')
            filename = f"{self.data_folder}/sensors_{ts}.json"
            with open(filename, 'w') as f:
                json.dump(readings, f)
            log_message(f"Data saved in {filename}")
            self._process_pending_data()
            gc.collect()
        except Exception as e:
            log_message(f"Error saving data: {e}")

    def _process_pending_data(self):
        try:
            files = sorted(f for f in os.listdir(self.data_folder) if f.startswith("sensors_"))
            count = 0
            for f in files:
                if count >= 5:
                    log_message("Batch limit reached, will process remaining files later")
                    break

                path = f"{self.data_folder}/{f}"
                with open(path, 'r') as file:
                    data = json.load(file)

                if self._send_via_uart(data):
                    os.remove(path)
                    log_message(f"Sent and removed {path}")
                    count += 1
                    time.sleep(0.5)
                else:
                    break

            log_message(f"Processed {count} pending files")
        except Exception as e:
            log_message(f"Error processing pending data: {e}")

    def retry_pending_data(self):
        self._process_pending_data()
