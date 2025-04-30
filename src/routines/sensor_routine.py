import ujson as json
import gc
import os
import time
import urequests
from readings.scheduler import SensorScheduler
from config.secrets import DEVICE_ID
from utils.logger import log_message


class SensorRoutine:
    def __init__(self, data_folder="data", device_id = DEVICE_ID):
        self.scheduler = SensorScheduler(settling_time=15)
        self.data_folder = data_folder
        self.device_id = DEVICE_ID 
        try:
            os.mkdir(data_folder)
        except OSError:
            pass
        
        self.scheduler.add_callback(self._save_data_callback)

        self._retry_flag = False

    def mark_retry_flag(self):
        self._retry_flag = True

    def should_retry(self):
        return self._retry_flag

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
    
    def _send_via_http(self, readings):
        try:
            gc.collect()
            url = "http://192.168.4.1/sensors/data"
            headers = {"Content-Type": "application/json"}
            payload = {
                "device_id": self.device_id,
                "timestamp": readings.get("timestamp", 0),
                "sensors": readings.get("data", readings.get("sensors", {}))
            }
            payload['aerator_status'] = readings.get('aerator_status', 'UNKNOWN')
            response = urequests.post(url, json=payload, headers=headers)
            status = response.status_code
            response.close()
            gc.collect()
            if status == 200:
                log_message("Data sent via HTTP successfully")
                return True
            else:
                log_message("HTTP POST failed with status:", status)
                return False
        except Exception as e:
            log_message("Error sending via HTTP:", e)
            gc.collect()
            return False

    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            log_message("No data to save")
            return

        try:
            timestamp_str = readings['timestamp']
            safe_timestamp_str = timestamp_str.replace(':', '-').replace('T', '_')
            filename = f"{self.data_folder}/sensors_{safe_timestamp_str}.json"
            with open(filename, 'w') as f:
                json.dump(readings, f)
            log_message(f"Data saved in {filename}")
            self._process_pending_data()
            gc.collect()
        except Exception as e:
            log_message(f"Error saving data: {e}")

    def _process_pending_data(self):
        try:
            files = [f for f in os.listdir(self.data_folder) if f.startswith("sensors_")]
            files.sort()  # Process oldest first
            
            files_processed = 0
            for filename in files:
                # Limit batch size to avoid overloading
                if files_processed >= 5:  # Process max 5 files per batch
                    log_message("Batch limit reached, will process remaining files later")
                    break
                    
                filepath = f"{self.data_folder}/{filename}"
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Try to send via HTTP
                if self._send_via_http(data):
                    # Only remove if successful
                    os.remove(filepath)
                    log_message(f"Sent and removed {filepath}")
                    files_processed += 1
                    
                    # Add delay between transmissions (500ms)
                    time.sleep(0.5)
                else:
                    # Stop trying if we hit a failure
                    break
                    
            log_message(f"Processed {files_processed} pending files")
        except Exception as e:
            log_message(f"Error processing pending data: {e}")


    # Add this method to allow manual retries
    def retry_pending_data(self):
        self._process_pending_data()
