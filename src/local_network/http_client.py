# src/local_network/http_client.py
import requests
import json

class HTTPClient:
    def __init__(self, server_ip='192.168.4.1'):
        self.base_url = f'http://{server_ip}'
        self.commands_endpoint = f'{self.base_url}/commands'
        self.data_endpoint = f'{self.base_url}/data'
        
    def send_sensor_data(self, data):
        try:
            response = requests.post(
                self.data_endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"HTTP send error: {e}")
            return False
            
    def check_commands(self, device_id):
        try:
            response = requests.get(
                f"{self.commands_endpoint}?device_id={device_id}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('commands', [])
        except Exception as e:
            print(f"HTTP command check error: {e}")
        return []
