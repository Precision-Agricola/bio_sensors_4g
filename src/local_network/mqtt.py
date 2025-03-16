# src/local_network/mqtt.py
import socket
import json
import time
from config.secrets import MQTT_CONFIG

class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sock = None
        self.connected = False
        self.subscribed_topics = set()
        
    def connect(self):
        try:
            self.sock = socket.socket()
            self.sock.connect((self.server, self.port))
            self._send_connect()
            if self._check_connack():
                self.connected = True
                return True
            else:
                self.sock.close()
                return False
        except Exception as e:
            print("MQTT connection error:", e)
            return False
    
    def _send_connect(self):
        import struct
        cmd = 0x10
        var_header = bytearray(b"\x00\x04MQTT\x04\x02\x00\x00")
        payload = bytearray()
        payload.extend(struct.pack("!H", len(self.client_id)))
        payload.extend(self.client_id.encode())
        
        if self.user:
            var_header[7] |= 0x80
            payload.extend(struct.pack("!H", len(self.user)))
            payload.extend(self.user.encode())
        
        if self.password:
            var_header[7] |= 0x40
            payload.extend(struct.pack("!H", len(self.password)))
            payload.extend(self.password.encode())
            
        remaining_length = len(var_header) + len(payload)
        rl = bytearray()
        while True:
            byte = remaining_length % 128
            remaining_length = remaining_length // 128
            if remaining_length > 0:
                byte |= 0x80
            rl.append(byte)
            if remaining_length == 0:
                break
        
        packet = bytearray([cmd])
        packet.extend(rl)
        packet.extend(var_header)
        packet.extend(payload)
        self.sock.send(packet)
    
    def _check_connack(self):
        resp = self.sock.recv(4)
        if resp and len(resp) == 4 and resp[0] == 0x20 and resp[3] == 0:
            return True
        return False
    
    def disconnect(self):
        if self.connected:
            self.sock.send(b"\xe0\0")
            self.sock.close()
            self.connected = False
    
    def subscribe(self, topic):
        if not self.connected:
            return False
            
        try:
            import struct
            cmd = 0x82
            packet_id = int(time.time()) % 65535
            var_header = struct.pack("!H", packet_id)
            payload = struct.pack("!H", len(topic)) + topic.encode() + b"\x00"
            
            remaining_length = len(var_header) + len(payload)
            rl = bytearray()
            while True:
                byte = remaining_length % 128
                remaining_length = remaining_length // 128
                if remaining_length > 0:
                    byte |= 0x80
                rl.append(byte)
                if remaining_length == 0:
                    break
            
            packet = bytearray([cmd])
            packet.extend(rl)
            packet.extend(var_header)
            packet.extend(payload)
            
            self.sock.send(packet)
            resp = self.sock.recv(5)
            
            if resp and len(resp) >= 4 and resp[0] == 0x90:
                self.subscribed_topics.add(topic)
                return True
            return False
        except Exception as e:
            print("Subscribe error:", e)
            return False
    
    def publish(self, topic, msg):
        if not self.connected:
            return False
            
        try:
            import struct
            cmd = 0x30
            var_header = struct.pack("!H", len(topic)) + topic.encode()
            payload = msg.encode() if isinstance(msg, str) else msg
            
            remaining_length = len(var_header) + len(payload)
            rl = bytearray()
            while True:
                byte = remaining_length % 128
                remaining_length = remaining_length // 128
                if remaining_length > 0:
                    byte |= 0x80
                rl.append(byte)
                if remaining_length == 0:
                    break
            
            packet = bytearray([cmd])
            packet.extend(rl)
            packet.extend(var_header)
            packet.extend(payload)
            
            self.sock.send(packet)
            return True
        except Exception as e:
            print("Publish error:", e)
            return False
            
    def check_msg(self, callback=None):
        if not self.connected:
            return None
            
        try:
            self.sock.settimeout(0.1)
            packet = self.sock.recv(1024)
            
            if not packet or len(packet) < 2:
                return None
                
            cmd = packet[0] & 0xF0
            
            if cmd == 0x30:
                if len(packet) < 4:
                    return None
                    
                remaining_length = packet[1]
                idx = 2
                
                if len(packet) <= idx + 2:
                    return None
                    
                topic_len = (packet[idx] << 8) | packet[idx + 1]
                idx += 2
                
                if len(packet) < idx + topic_len:
                    return None
                    
                topic = packet[idx:idx + topic_len]
                topic_str = topic.decode('utf-8', 'ignore')
                idx += topic_len
                
                if idx < len(packet):
                    payload = packet[idx:]
                    
                    if callback:
                        callback(topic_str, payload)
                    
                    return (topic_str, payload)
            
            return None
        except Exception as e:
            if not isinstance(e, OSError) or e.args[0] != 110:  # ETIMEDOUT
                print("Check msg error:", e)
            return None

class MQTTManager:
    def __init__(self):
        self.client_id = MQTT_CONFIG.get("client_id", "sensor_device")
        self.broker = MQTT_CONFIG.get("broker", "192.168.4.1")
        self.port = MQTT_CONFIG.get("port", 1883)
        self.topic = MQTT_CONFIG.get("topic", "sensor/readings")
        self.command_topic = f"command/{self.client_id}"
        self.all_commands_topic = "command/all"
        self.response_topic = f"response/{self.client_id}"
        self.username = MQTT_CONFIG.get("username", None)
        self.password = MQTT_CONFIG.get("password", None)
        self.client = None
        self.command_handlers = {}
        
    def connect(self):
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
            
    def publish(self, data):
        try:
            if isinstance(data, dict) and "device_id" not in data:
                data["device_id"] = self.client_id
            
            json_payload = json.dumps(data)
            
            if not self.client or not self.client.connected:
                if not self.connect():
                    return False
            
            return self.client.publish(self.topic, json_payload)
        except Exception as e:
            print("MQTT publish error:", e)
            return False
    
    def register_command_handler(self, command, handler):
        if callable(handler):
            self.command_handlers[command] = handler
            return True
        return False
    
    def start_command_listener(self):
        if not self.client or not self.client.connected:
            if not self.connect():
                return False
                
        if self.client.subscribe(self.command_topic) and self.client.subscribe(self.all_commands_topic):
            return True
        return False
    
    def check_commands(self):
        if not self.client or not self.client.connected:
            return False
            
        return self.client.check_msg(self._handle_message) is not None
    
    def _handle_message(self, topic, payload):
        try:
            message = payload.decode('utf-8', 'ignore')
            data = json.loads(message)
            
            if topic == self.command_topic or topic == self.all_commands_topic:
                command = data.get("command")
                
                if command == "READ_NOW":
                    if "READ_NOW" in self.command_handlers:
                        result = self.command_handlers["READ_NOW"](data.get("params", {}))
                        self._send_response(data, {"status": "OK", "readings": result})
                    else:
                        self._send_response(data, {"status": "ERROR", "message": "Handler not registered"})
                elif command in self.command_handlers:
                    result = self.command_handlers[command](data.get("params", {}))
                    self._send_response(data, {"status": "OK", "result": result})
                else:
                    self._send_response(data, {"status": "ERROR", "message": f"Unknown command: {command}"})
        except Exception as e:
            print("Error processing message:", e)
    
    def _send_response(self, cmd_data, response_data):
        response = {
            "command_id": cmd_data.get("command_id", "unknown"),
            "device_id": self.client_id,
            "timestamp": time.time(),
            "response": response_data
        }
        
        if not self.client or not self.client.connected:
            if not self.connect():
                return False
                
        return self.client.publish(self.response_topic, json.dumps(response))
