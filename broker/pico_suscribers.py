# Simple MQTT subscriber for Pico W
import network
from umqtt.simple import MQTTClient
from config.secrets import WIFI_CONFIG, MQTT_CONFIG

# WiFi Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_CONFIG["ssid"], WIFI_CONFIG["password"])
while not wlan.isconnected():
    pass
print("WiFi Connected:", wlan.ifconfig())

# MQTT Callback
def on_message(topic, msg):
    print(f"Topic: {topic.decode()}\nMessage: {msg.decode()}")

# Connect to Broker
client = MQTTClient(
    client_id="pico_subscriber",
    server=MQTT_CONFIG["broker"],
    port=MQTT_CONFIG["port"]
)
client.set_callback(on_message)
client.connect()
client.subscribe(MQTT_CONFIG["topic"])

# Listen Forever
while True:
    client.wait_msg()  # Non-blocking wait
