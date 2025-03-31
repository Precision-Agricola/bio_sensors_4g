import ujson as json
import gc
import os
import time
import urequests
from readings.scheduler import SensorScheduler
from config.secrets import DEVICE_ID

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
        
    def start(self):
        print("Starting sensor routine...")
        return self.scheduler.start()
    
    def stop(self):
        print("Stopping sensor routine...")
        return self.scheduler.stop()
    
    def read_now(self):
        print("Performing immediate sensor reading...")
        return self.scheduler.read_now()
    
    def _send_via_http(self, readings):
        """
        Send sensor readings to the local server endpoint that posts to AWS IoT Core.
        The server endpoint is expected to be:
            POST http://192.168.4.1/sensors/data
        """
        try:
            url = "http://192.168.4.1/sensors/data"
            headers = {"Content-Type": "application/json"}
            payload = {
                "device_id": self.device_id,
                "timestamp": readings.get("timestamp", 0),
                "sensors": readings.get("data", readings.get("sensors", {}))
            }
            response = urequests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print("Data sent via HTTP successfully")
                response.close()
                return True
            else:
                print("HTTP POST failed with status:", response.status_code)
                response.close()
                return False
        except Exception as e:
            print("Error sending via HTTP:", e)
            return False

    def _save_data_callback(self, readings):
        if not readings or 'data' not in readings:
            print("No data to save")
            return
            
        try:
            timestamp = readings['timestamp']
            filename = f"{self.data_folder}/sensors_{int(timestamp)}.json"
            with open(filename, 'w') as f:
                json.dump(readings, f)
            print(f"Data saved in {filename}")
            
            # Try to send this reading and also process any pending files
            self._process_pending_data()
            
            gc.collect()
        except Exception as e:
            print(f"Error saving data: {e}")

    def _process_pending_data(self):
        try:
            files = [f for f in os.listdir(self.data_folder) if f.startswith("sensors_")]
            files.sort()  # Process oldest first
            
            files_processed = 0
            for filename in files:
                # Limit batch size to avoid overloading
                if files_processed >= 5:  # Process max 5 files per batch
                    print("Batch limit reached, will process remaining files later")
                    break
                    
                filepath = f"{self.data_folder}/{filename}"
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Try to send via HTTP
                if self._send_via_http(data):
                    # Only remove if successful
                    os.remove(filepath)
                    print(f"Sent and removed {filepath}")
                    files_processed += 1
                    
                    # Add delay between transmissions (500ms)
                    time.sleep(0.5)
                else:
                    # Stop trying if we hit a failure
                    break
                    
            print(f"Processed {files_processed} pending files")
        except Exception as e:
            print(f"Error processing pending data: {e}")


    # Add this method to allow manual retries
    def retry_pending_data(self):
        print("Retrying to send pending data...")
        self._process_pending_data()
