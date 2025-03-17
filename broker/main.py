# broker/main.py
"""HTTP Server for Raspberry Pi Pico W with AWS IoT Core integration

This script sets up an HTTP server to receive sensor data and forward it to AWS IoT Core.
It also serves as a command relay to devices.
"""
import time
import gc
from machine import Pin, WDT

# Import core modules
from core.access_point import setup_access_point
from core.http_server import start_server
from core.stats import print_stats

# Configuration
SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"
HTTP_PORT = 80

def main():
    try:
        wdt = WDT(timeout=80000)
    except:
        wdt = None
        print("Watchdog timer not available")
    ap = setup_access_point(SSID, PASSWORD)
    stats_timer = time.time()
    try:
        start_server(port=HTTP_PORT)
    except Exception as e:
        print(f"Server error: {e}")
        import sys
        sys.print_exception(e)
        while True:
            try:
                if time.time() - stats_timer > 60:
                    print_stats()
                    stats_timer = time.time()
                    
                if wdt:
                    wdt.feed()
                    
                gc.collect()
                    
                time.sleep(1)
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    main()
