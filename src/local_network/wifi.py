"""WiFi Manager"""
# src/local_network/wifi.py
import network
import time
import os
import gc

def connect_wifi(ssid="PrecisionAgricola", password="ag2025pass", timeout=15, force_reconnect=False):
    """Connect to WiFi network in station mode with improved error handling."""
    wlan = network.WLAN(network.STA_IF)

    #TODO: remove the try catch once the configuration values are well-defined
    try:
        wlan.config(reconnects=5)
    except Exception as e:
        print(f"Wlan configuration error on reconnect: {str(e)}") 

    try:
        wlan.config(txpower=19) #  76,// 19dBm
    except Exception as e:
        print(f"Wlan config error on txpower: {str(e)}")

    if force_reconnect and wlan.isconnected():
        print("Desconectando WiFi para reconexión forzada...")
        wlan.disconnect()
        time.sleep(1)
    
    if not wlan.active():
        wlan.active(True)
        time.sleep(1)
    
    if wlan.isconnected():
        print(f"Already connected to {ssid}")
        return True
    
    gc.collect()
    
    print(f"Connecting to {ssid}...")
    try:
        wlan.connect(ssid, password)
    except OSError as e:
        print(f"Error inicial al conectar: {e}")
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        time.sleep(1)
        try:
            wlan.connect(ssid, password)
        except Exception as e2:
            print(f"Segundo error al conectar: {e2}")
            return False
    
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print(f"Failed to connect to {ssid} (timeout)")
            try:
                wlan.disconnect()
            except:
                pass
            return False
        time.sleep(0.5)
    
    print(f"Connected to {ssid}")
    print(f"IP: {wlan.ifconfig()[0]}")
    return True

def reset_wifi():
    """Reset completo del módulo WiFi"""
    import network
    import time
    import machine
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)
    
    if not connect_wifi(timeout=10):
        print("Reiniciando el ESP32...")
        machine.reset()


def verify_wifi_connection():
    """Verifica la conexión WiFi periódicamente y reconecta si es necesario"""
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("Conexión WiFi perdida, reconectando...")
        connect_wifi(force_reconnect=True)
    return wlan.isconnected()


def save_to_backup(data):
    """Save data to backup file."""
    try:
        try:
            os.mkdir("data")
        except OSError:
            pass
        try:
            os.mkdir("data/backup")
        except OSError:
            pass
            
        filename = f"data/backup/data_{int(time.time())}.json"
        
        with open(filename, "w") as f:
            f.write(data)
            
        print(f"Data saved to backup: {filename}")
    except Exception as e:
        print(f"Error saving backup: {e}")
