"""MQTT Broker for Raspberry Pi Pico W

Receives sensor data from ESP32 devices for Precision Agrícola
"""
import network
import socket
import time
import json
from machine import Pin
import gc

# WiFi Access Point config
SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"  # Change to a secure password

# MQTT configuration
MQTT_PORT = 1883
MQTT_TOPIC = b"sensor/readings"

# LED for status indication
led = Pin("LED", Pin.OUT)

# Storage for received data
received_data = []
MAX_STORED_MESSAGES = 100

def setup_access_point():
    """Set up Pico W as an access point"""
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)
    
    while not ap.active:
        pass
    
    print("Access point active")
    print(f"SSID: {SSID}")
    print(f"IP address: {ap.ifconfig()[0]}")
    return ap

def start_mqtt_broker():
    """Start a simple MQTT broker"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', MQTT_PORT))
    s.listen(5)
    print(f"MQTT broker listening on port {MQTT_PORT}")
    return s

def handle_mqtt_packet(payload):
    """Process received MQTT payload data"""
    try:
        # Decode and parse JSON
        message = payload.decode('utf-8', 'ignore')
        data = json.loads(message)
        
        # Store the data
        if len(received_data) >= MAX_STORED_MESSAGES:
            received_data.pop(0)  # Remove oldest message if at capacity
        received_data.append(data)
        
        # Print basic info
        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp", 0)
        print(f"Data from {device_id} at {timestamp}")
        
        # Flash LED to indicate data received
        led.toggle()
        
        return True
    except Exception as e:
        print(f"Error processing message: {e}")
        return False

def handle_mqtt(client_socket):
    """Handle basic MQTT protocol"""
    try:
        # Set socket timeout
        client_socket.settimeout(3)
        
        # Read first packet (should be CONNECT)
        packet = client_socket.recv(1024)
        
        if not packet or len(packet) < 2:
            return
        
        # Check if first byte is CONNECT (0x10)
        if packet[0] == 0x10:
            # Send CONNACK
            client_socket.write(b"\x20\x02\x00\x00")
            print("Client connected")
            
            # Listen for PUBLISH packets
            while True:
                try:
                    packet = client_socket.recv(1024)
                    
                    if not packet or len(packet) < 2:
                        break
                    
                    # Check if PUBLISH packet (0x30)
                    if (packet[0] & 0xF0) == 0x30:
                        # Extract message (simplified)
                        # Real MQTT would parse variable length properly
                        idx = 2  # Skip command and length
                        
                        # Skip topic length + topic
                        if len(packet) > idx + 2:
                            topic_len = (packet[idx] << 8) | packet[idx + 1]
                            idx += 2 + topic_len
                            
                            # Get payload
                            if len(packet) > idx:
                                payload = packet[idx:]
                                handle_mqtt_packet(payload)
                except Exception as e:
                    print(f"Error reading packet: {e}")
                    break
    
    except Exception as e:
        print(f"MQTT handling error: {e}")
    
    finally:
        try:
            client_socket.close()
        except:
            pass

def get_stored_data():
    """Get all stored sensor data"""
    return received_data

def main():
    # Set up access point
    ap = setup_access_point()
    
    # Start MQTT broker
    broker_socket = start_mqtt_broker()
    
    print("MQTT broker ready")
    
    while True:
        try:
            # Accept client connection
            client, addr = broker_socket.accept()
            print(f"Connection from {addr}")
            
            # Handle MQTT communication
            handle_mqtt(client)
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            print(f"Server error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()