"""Access Point core utility"""
from config.secrets import WIFI_CONFIG
import network
import time

def setup_access_point(
        ssid:str = WIFI_CONFIG.get("ssid", "PrecisionAgricola"),
        password:str = WIFI_CONFIG.get("password", "ag2025pass")
        ):

    ap = network.WLAN(network.AP_IF)
    ap.config(
        essid=ssid,
        password=password,
        )
    ap.active(True)

    timeout = 10
    start_time = time.time()
    while not ap.active():
        if time.time() - start_time > timeout:
            raise RuntimeError(f"Failed to activate access point at timeout: {timeout}")
        time.sleep(0.1)

    print("\n=== WiFi Access Point Active ===")
    print(f"SSID: {ssid}")
    print(f"IP Address: {ap.ifconfig()[0]}")
    print(f"Subnet Mask: {ap.ifconfig()[1]}")
    print(f"Gateway: {ap.ifconfig()[2]}")
    print(f"DNS: {ap.ifconfig()[3]}")
    print("================================\n")
    
    return ap