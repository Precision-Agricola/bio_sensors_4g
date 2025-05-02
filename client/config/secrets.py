import machine

def get_mac_suffix():
    mac = machine.unique_id()
    return ''.join('{:02x}'.format(b) for b in mac[-3:]).upper()

# Device identification (HTTP)
DEVICE_ID = f"ESP32_{get_mac_suffix()}"
SERVER_IP = "192.168.4.1"
SERVER_PORT = 80 

# WiFi configuration
WIFI_CONFIG = {
    "ssid": "PrecisionAgricola",  # Access point SSID
    "password": "ag2025pass",     # Access point password
    "ws_server_uri": "ws://192.168.4.1/ws" # websocket server uri
}

# Broker IP (Microdot HTTP server)
BROKER_IP = "192.168.4.1"
