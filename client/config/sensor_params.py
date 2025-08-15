# client/config/sensor_params.py
# TODO: implement the sensors params in the respective sensor readings

# PH sensor
PH_SIGNAL = 32
PH_SAMPLES = 5

# liquid flow
LIQUID_FLOW = 18

# Adc converter
ADC_NH3_CHANNEL = 3
ADC_H2S_CHANNEL = 0

# I2C devices
I2C_BMP_ADDRESS = [0x76, 0x77]
I2C_ADS_ADDRESS = [0x46]

# RS484 sensor
RS485_TX = 1
RS485_RX = 3
RS485_DE_RE = 22
