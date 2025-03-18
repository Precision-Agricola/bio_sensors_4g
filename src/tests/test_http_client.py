"""Testing http client"""

from local_network.http_client import HTTPClient
import time
import json

def test_http_client():
    """Test the HTTP client connection"""
    # Create client with explicit parameters to avoid any config issues
    client = HTTPClient(server_ip="192.168.4.1", server_port=80)
    
    test_data = {
        "device_id": "ESP32_TEST_CLIENT",
        "timestamp": time.time(),
        "data": {
            "temperature": 255,
            "humidity": 60.2,
            "pressure": 1013.25
        }
    }
    
    print(f"Using server URL: {client.server_url}")
    print("Connecting to WiFi...")
    
    if not client.connect():
        print("Failed to connect to WiFi")
        return False
    
    print(f"Connected! Sending test data to broker...")
    success = client.send_data(test_data)
    
    if success:
        print("Test successful! Data sent to broker.")
    else:
        print("Test failed. Could not send data to broker.")
    
    return success

if __name__ == "__main__":
    test_http_client()
