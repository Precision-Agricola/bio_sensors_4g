import network
import time
from umqtt.simple import MQTTClient

SSID = "RedTest"
PASSWORD = "password123"
BROKER = "192.168.1.10"

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Conectado:", wlan.ifconfig())
    return wlan

wlan = conectar_wifi()

client = MQTTClient("esp32_pub", BROKER)
try:
    client.connect()
    print("Conectado al broker MQTT")
except Exception as e:
    print("Error al conectar al broker:", e)

while True:
    mensaje = b"Hola desde ESP32"
    try:
        client.publish(b"topic/test", mensaje)
        print("Mensaje publicado:", mensaje)
    except Exception as e:
        print("Error publicando:", e)
    time.sleep(5)
