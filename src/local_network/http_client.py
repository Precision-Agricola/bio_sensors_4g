"""Http client using urequest to interact with the raspberry pi pico http server"""
# src/local_network/http_client.py

import urequests
import json
import time
import os
from local_network.wifi import connect_wifi
from config.secrets import DEVICE_ID
SERVER_IP = "192.168.4.1"
SERVER_PORT = 80 

class HTTPClient:
    def __init__(self, server_ip=SERVER_IP, server_port=SERVER_PORT, retry_count=3, backup_folder="data/backup"):
        """Initialize HTTP client to connect to the broker."""
        self.server_url = f"http://{server_ip}:{server_port}"
        self.retry_count = retry_count
        self.backup_folder = backup_folder

        try:
            os.mkdir("data")
        except OSError:
            pass
            
        try:
            os.mkdir(backup_folder)
        except OSError:
            pass
        
    def connect(self):
        """Ensure WiFi connection to the broker"""
        return connect_wifi()
        
    def send_data(self, data, timeout=5):
        """Send sensor data to the broker via HTTP POST with enhanced error handling"""
        if not self.connect():
            print("Primer intento de conexión fallido, intentando reconexión forzada...")
            import local_network.wifi as wifi
            if not wifi.connect_wifi(force_reconnect=True, timeout=15):
                print("Reconexión forzada fallida, guardando en backup...")
                self._save_backup(data)
                return False
            
        if isinstance(data, dict) and "device_id" not in data:
            if DEVICE_ID:
                data["device_id"] = DEVICE_ID
            else:
                data["device_id"] = "unknown"
        
        if isinstance(data, dict) and "timestamp" not in data:
            data["timestamp"] = time.time()
            
        for attempt in range(self.retry_count):
            try:
                url = f"{self.server_url}/sensors/data"
                headers = {'Content-Type': 'application/json'}
                
                print(f"Sending data to {url}, attempt {attempt+1}/{self.retry_count}")
                
                try:
                    response = urequests.post(url, headers=headers, json=data, timeout=timeout)
                    success = 200 <= response.status_code < 300
                    print(f"Response status: {response.status_code}")
                    response.close()
                    
                    if success:
                        print(f"Data sent successfully on attempt {attempt+1}")
                        self._send_backups()
                        return True
                        
                    print(f"Server returned error status: {response.status_code}, retrying...")
                except OSError as e:
                    if e.errno == 116:  # ETIMEDOUT
                        print("Connection timed out, but data may have been received.")
                        print("Treating as potential success after timeout error.")
                        print("WARNING: Assuming data was sent successfully despite timeout")
                        return True
                    else:
                        raise
                    
                time.sleep(1)
                    
            except Exception as e:
                print(f"HTTP error on attempt {attempt+1}: {e}")
                time.sleep(1)
        
        self._save_backup(data)
        return False

    def _save_backup(self, data):
        """Save data for later retry"""
        try:
            timestamp = int(time.time())
            filename = f"{self.backup_folder}/data_{timestamp}.json"
            
            with open(filename, 'w') as f:
                if isinstance(data, dict) or isinstance(data, list):
                    json.dump(data, f)
                else:
                    f.write(data)
                    
            print(f"Data saved to backup: {filename}")
            return True
        except Exception as e:
            print(f"Error saving backup: {e}")
            return False
    
    def _send_backups(self):
        """Try to send backed up data"""
        try:
            files = os.listdir(self.backup_folder)
            if not files:
                return
                
            print(f"Found {len(files)} backup files to send")
            
            for filename in files:
                if not filename.endswith('.json'):
                    continue
                    
                filepath = f"{self.backup_folder}/{filename}"
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        
                    url = f"{self.server_url}/sensors/data"
                    headers = {'Content-Type': 'application/json'}
                    
                    response = urequests.post(url, headers=headers, json=data, timeout=5)
                    success = 200 <= response.status_code < 300
                    response.close()
                    
                    if success:
                        print(f"Successfully sent backup: {filename}")
                        os.remove(filepath)
                    else:
                        print(f"Failed to send backup: {filename}")
                        
                except Exception as e:
                    print(f"Error processing backup {filename}: {e}")
                    
        except Exception as e:
            print(f"Error in send_backups: {e}")
    