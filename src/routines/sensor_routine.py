import ujson as json
import gc
import os
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
            
            self._send_via_http(readings)
            
            gc.collect()
        except Exception as e:
            print(f"Error saving data: {e}")
