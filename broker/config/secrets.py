WIFI_CONFIG = {
    "ssid": "bio_sensors_access_point",
    "password": "#ExitoAgricola1$"
}

DEVICE_SERIAL = {
    "device_id": "0001"
}

MQTT_CONFIG = {
    "broker": "192.168.4.100",
    "port": 1883,
    "client_id": DEVICE_SERIAL["device_id"],
    "topic": "sensors/data",
    "qos": 1
}
