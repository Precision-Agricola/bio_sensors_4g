"""MQTT Manager for sensor data transmission"""
import socket
import json
import time
from config.secrets import MQTT_CONFIG
from local_network.wifi import save_to_backup

class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None, keepalive=0):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.sock = None
        self.connected = False
        
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
        if self.user:
            var_header[7] |= 0x80
            payload.extend(struct.pack("!H", len(self.user)))
            payload.extend(self.user.encode())
        
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
        self.sock.write(packet)
    
    def _check_connack(self):
        # Read CONNACK
        resp = self.sock.read(4)
        if resp and len(resp) == 4 and resp[0] == 0x20 and resp[3] == 0:
            self.connected = True
            return True
        return False
    
    def connect(self):
        import socket
        
        # Create socket
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        
        # Send CONNECT
        self._send_connect()
        
        # Check CONNACK
        if self._check_connack():
            return True
        else:
            self.sock.close()
            return False
    
    def disconnect(self):
        if self.connected:
            # DISCONNECT packet
            self.sock.write(b"\xe0\0")
            self.sock.close()
            self.connected = False
    
    def publish(self, topic, msg):
        if not self.connected:
            return False
        
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
        self.sock.write(packet)
        return True

class MQTTManager:
    def __init__(self):
        """Initialize MQTT Manager with configuration from secrets."""
        self.client_id = MQTT_CONFIG.get("client_id", "sensor_device")
        self.broker = MQTT_CONFIG.get("broker", "192.168.4.1")
        self.port = MQTT_CONFIG.get("port", 1883)
        self.topic = MQTT_CONFIG.get("topic", "sensor/readings")
        self.username = MQTT_CONFIG.get("username", None)
        self.password = MQTT_CONFIG.get("password", None)
        self.client = None
        
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = MQTTClient(
                self.client_id, 
                self.broker, 
                self.port,
                self.username,
                self.password
            )
            return self.client.connect()
        except Exception as e:
            print("MQTT connection error:", e)
            return False
            
    def publish(self, payload):
        """Publish sensor data to MQTT broker.
        
        Args:
            payload (dict): Data to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert payload to JSON
            json_payload = json.dumps(payload)
            
            # Connect if not connected
            if not self.client or not self.client.connected:
                if not self.connect():
                    save_to_backup(json_payload)
                    return False
            
            # Publish message
            result = self.client.publish(self.topic, json_payload)
            
            # Disconnect to save resources
            self.client.disconnect()
            
            return result
        except Exception as e:
            print("MQTT publish error:", e)
            
            # Save to backup if publishing fails
            save_to_backup(json_payload)
            return False