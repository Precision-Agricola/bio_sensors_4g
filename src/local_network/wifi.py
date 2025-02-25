"""WiFi Manager"""

import network
import urequests
import time
import os
import socket
from config.secrets import WIFI_CONFIG, SERVER_CONFIG, MQTT_CONFIG

# Backup file name
BACKUP_FILE = "backup_data.json"

def connect():
    """Connect to the WiFi network with timeout and error handling."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        print(f"Attempting connection to SSID: {WIFI_CONFIG['ssid']}")
        try:
            wlan.connect(WIFI_CONFIG["ssid"], WIFI_CONFIG["password"])
            # Wait for connection with a 10-second timeout
            start_time = time.time()
            while not wlan.isconnected():
                if time.time() - start_time > 10:
                    raise Exception("WiFi connection timeout")
                time.sleep(0.1)
        except Exception as e:
            print("WiFi connection failed:", e)
            return False
    print("WiFi connected")
    # Print network info for debugging
    ip, subnet, gateway, dns = wlan.ifconfig()
    print(f"IP: {ip}, Gateway: {gateway}")
    print(f"Trying to ping MQTT broker at {MQTT_CONFIG['broker']}")
    # Try simple socket connection to verify
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((MQTT_CONFIG['broker'], MQTT_CONFIG['port']))
        s.close()
        print("MQTT broker is reachable")
    except Exception as e:
        print(f"Cannot reach MQTT broker: {e}")
    return True


def save_to_backup(payload):
    """Append the payload to the backup file."""
    try:
        with open(BACKUP_FILE, "a") as f:
            f.write(payload + "\n")
        print("Data saved to backup")
    except Exception as e:
        print("Error saving to backup:", e)

def get_backup_data():
    """Read all lines from the backup file."""
    try:
        with open(BACKUP_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except Exception:
        # File doesn’t exist or error occurred
        return []

def clear_backup():
    """Clear the backup file."""
    try:
        os.remove(BACKUP_FILE)
        print("Backup cleared")
    except Exception as e:
        print("Error clearing backup:", e)

def send_data(payload):
    """Send the payload to the server, handling backups if necessary."""
    if not connect():
        # If connection fails, save to backup and exit
        save_to_backup(payload)
        return

    # Send any backed-up data first
    backup_data = get_backup_data()
    if backup_data:
        print(f"Sending {len(backup_data)} backed-up payloads")
        for data in backup_data:
            try:
                response = urequests.post(SERVER_CONFIG["url"], data=data)
                print("Backup data sent successfully:", response.text)
            except Exception as e:
                print("Error sending backup data:", e)
                # If sending backup fails, save new payload and stop
                save_to_backup(payload)
                return

    # Send the current payload
    try:
        response = urequests.post(SERVER_CONFIG["url"], data=payload)
        print("Data sent successfully:", response.text)
        # If all data sent successfully, clear the backup
        if backup_data:
            clear_backup()
    except Exception as e:
        print("Error sending data:", e)
        save_to_backup(payload)
