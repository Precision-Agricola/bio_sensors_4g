"""MQTT Manager"""
import socket
import json
import time
from config.secrets import MQTT_CONFIG

class MQTTManager:
    def __init__(self):
        """Initialize MQTT Manager with configuration from secrets."""
        self.client_id = MQTT_CONFIG.get("client_id", "sensor_device")
        self.broker = MQTT_CONFIG.get("broker", "192.168.4.1")  # IP del Raspberry Pi Pico W (AP)
        self.port = MQTT_CONFIG.get("port", 1883)
        self.topic = MQTT_CONFIG.get("topic", "sensor/readings")
        self.username = MQTT_CONFIG.get("username", None)
        self.password = MQTT_CONFIG.get("password", None)
        self.client = None
        
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.broker, self.port))
            self._send_connect()
            if self._check_connack():
                return True
            else:
                self.client.close()
                return False
        except Exception as e:
            print("MQTT connection error:", e)
            return False
            
    def _send_connect(self):
        import struct
        
        # Fixed header
        cmd = 0x10  # CONNECT command
        
        # Variable header and payload
        var_header = bytearray(b"\x00\x04MQTT\x04\x02\x00\x00")
        payload = bytearray()
        
        # Add client ID
        payload.extend(struct.pack("!H", len(self.client_id)))
        payload.extend(self.client_id.encode())
        
        # Add username if set
        if self.username:
            var_header[7] |= 0x80
            payload.extend(struct.pack("!H", len(self.username)))
            payload.extend(self.username.encode())
        
        # Add password if set
        if self.password:
            var_header[7] |= 0x40
            payload.extend(struct.pack("!H", len(self.password)))
            payload.extend(self.password.encode())
        
        # Calculate remaining length
        remaining_length = len(var_header) + len(payload)
        
        # Encode remaining length
        rl = bytearray()
        while True:
            byte = remaining_length % 128
            remaining_length = remaining_length // 128
            if remaining_length > 0:
                byte |= 0x80
            rl.append(byte)
            if remaining_length == 0:
                break
        
        # Construct packet
        packet = bytearray([cmd])
        packet.extend(rl)
        packet.extend(var_header)
        packet.extend(payload)
        
        # Send packet
        self.client.send(packet)
    
    def _check_connack(self):
        # Read CONNACK
        resp = self.client.recv(4)
        if resp and len(resp) == 4 and resp[0] == 0x20 and resp[3] == 0:
            return True
        return False
    
    def disconnect(self):
        if self.client:
            # DISCONNECT packet
            self.client.send(b"\xe0\0")
            self.client.close()
            self.client = None
    
    def publish(self, data):
        """Publish sensor data to MQTT broker.
        
        Args:
            data (dict): Data to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert payload to JSON
            json_payload = json.dumps(data)
            
            # Connect if not connected
            if not self.client:
                if not self.connect():
                    self._save_to_backup(data)
                    return False
            
            # Publish message
            result = self._publish_message(self.topic, json_payload)
            
            # Disconnect to save resources
            self.disconnect()
            
            return result
        except Exception as e:
            print("MQTT publish error:", e)
            
            # Save to backup if publishing fails
            self._save_to_backup(data)
            return False
            
    def _publish_message(self, topic, msg):
        import struct
        
        # Fixed header
        cmd = 0x30  # PUBLISH command
        
        # Variable header and payload
        var_header = struct.pack("!H", len(topic)) + topic.encode()
        payload = msg.encode() if isinstance(msg, str) else msg
        
        # Calculate remaining length
        remaining_length = len(var_header) + len(payload)
        
        # Encode remaining length
        rl = bytearray()
        while True:
            byte = remaining_length % 128
            remaining_length = remaining_length // 128
            if remaining_length > 0:
                byte |= 0x80
            rl.append(byte)
            if remaining_length == 0:
                break
        
        # Construct packet
        packet = bytearray([cmd])
        packet.extend(rl)
        packet.extend(var_header)
        packet.extend(payload)
        
        # Send packet
        self.client.send(packet)
        return True
        
    def _save_to_backup(self, data):
        """Save data to backup file if MQTT fails."""
        try:
            import os
            # Ensure backup directory exists
            try:
                os.mkdir("/data/backup")
            except:
                pass
                
            # Create backup filename with timestamp
            filename = f"/data/backup/mqtt_{int(time.time())}.json"
            
            # Write data to file
            with open(filename, "w") as f:
                json.dump(data, f)
                
            print(f"Data saved to backup: {filename}")
        except Exception as e:
            print(f"Error saving backup: {e}")