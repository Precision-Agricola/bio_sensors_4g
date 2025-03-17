"""WiFi Manager"""

# src/local_network/wifi.py
import network
import time
import json
import os

def connect_wifi(ssid="PrecisionAgricola", password="ag2025pass", timeout=10):
    """Connect to WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Check if already connected
    if wlan.isconnected():
        print(f"Already connected to {ssid}")
        return True
    
    print(f"Connecting to {ssid}...")
    wlan.connect(ssid, password)
    
    # Wait for connection with timeout
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print(f"Failed to connect to {ssid} (timeout)")
            return False
        time.sleep(0.1)
    
    print(f"Connected to {ssid}")
    print(f"IP: {wlan.ifconfig()[0]}")
    return True

def save_to_backup(data):
    """Save data to backup file."""
    try:
        # Ensure backup directory exists
        try:
            os.mkdir("/data/backup")
        except:
            pass
            
        # Create backup filename with timestamp
        filename = f"/data/backup/mqtt_{int(time.time())}.json"
        
        # Write data to file
        with open(filename, "w") as f:
            f.write(data)
            
        print(f"Data saved to backup: {filename}")
    except Exception as e:
        print(f"Error saving backup: {e}")

def get_ip_address():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return None
