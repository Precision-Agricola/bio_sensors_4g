"""MQTT Broker para Raspberry Pi Pico W con integración AWS IoT Core

Este script actúa como broker MQTT local y retransmite los datos a AWS IoT Core.
Recibe datos de sensores a través del punto de acceso local y los reenvía a AWS.
"""

from core.wifi import setup_access_point
from core.mqtt_broker import start_mqtt_broker, handle_client
from core.utils import print_stats
import time, gc

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"
MQTT_PORT = 1883

def main():
    setup_access_point(SSID, PASSWORD)
    broker = start_mqtt_broker(MQTT_PORT)
    stats_timer = time.time()
    stats = {"messages":0, "errors":0, "aws_success":0, "aws_error":0}
    last_seen = {}
    print("Broker listo.")

    while True:
        try:
            broker.settimeout(5)
            try:
                client, _ = broker.accept()
                handle_client(client, stats, last_seen)
            except OSError:
                pass
            if time.time() - stats_timer > 60:
                print_stats(stats, last_seen)
                stats_timer = time.time()
            gc.collect()
        except Exception as e:
            print(f"Error server: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
