import json

RTC_CLK_PIN = 16
RTC_DIO_PIN = 21
RTC_CS_PIN = 23
I2C_BUS_ID = 1
I2C_SCL_PIN = 23
I2C_SDA_PIN = 21
AERATOR_PIN_A = 12
AERATOR_PIN_B = 27

WIFI_CONFIG = {
  "server_ip": "192.168.4.1",
  "sever_port": 8080
}

def load_device_config(config_file='config/device_config.json'):
    try:
        with open(config_file) as f:
            return json.load(f)
    except:
        print('Error loading device config')
        return {
            'wifi': {'ssid': '', 'password': ''},
            'server_ip': '192.168.1.100',
            'port': 5000
        }
