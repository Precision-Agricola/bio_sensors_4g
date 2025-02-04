# ESP32 Sensor Data Collection System

A modular MicroPython-based system for collecting data from various sensors and transmitting it to a Raspberry Pi via WiFi.

## Project Structure

    project_root/
    ├── src/
    │   ├── main.py              # Main execution script
    │   ├── config.py            # Configuration parameters
    │   ├── sensors/             # Sensor implementations
    │   │   ├── base.py          # Base sensor class
    │   │   ├── temperature/     # Temperature sensors
    │   │   ├── pressure/        # Pressure sensors
    │   │   └── protocols/       # Communication protocols
    │   └── network/             # Network communication
    ├── tests/                   # Unit tests
    └── docs/                    # Documentation

## Installation

1. Install MicroPython on your ESP32:
    ```bash
    esptool.py --port /dev/ttyUSB0 erase_flash
    esptool.py --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-{version}.bin
    ```

2. Upload the project files:
    ```bash
    ampy --port /dev/ttyUSB0 put src/
    ```

3. Configure your WiFi credentials in config.py

## Configuration

Edit `config.py` to set up your device:

    # config.py
    WIFI_SSID = "your_network_name"
    WIFI_PASSWORD = "your_password"
    
    # Reading intervals (in seconds)
    READING_INTERVAL = 30
    
    # Sensor pins configuration
    SENSOR_PINS = {
        "scd41_i2c_scl": 22,
        "scd41_i2c_sda": 21,
        "thermistor_analog": 32
    }

## Adding New Sensors

### 1. Create a New Sensor Class

Create a new file in the appropriate category folder (e.g., `sensors/temperature/new_sensor.py`):

    from ..base import SensorBase
    from machine import Pin, I2C  # or other required hardware interfaces
    
    class NewSensor(SensorBase):
        def __init__(self, pin_or_i2c, name="NewSensor"):
            super().__init__(name)
            self.hardware = pin_or_i2c
            
        def initialize(self):
            try:
                # Initialize your sensor here
                # Return True if successful
                self.connected = True
                return True
            except Exception as e:
                print("Init error:", str(e))
                self.connected = False
                return False
        
        def read(self):
            if not self.connected:
                return None
                
            try:
                # Read your sensor here
                # Return data in dictionary format
                return {
                    "temperature": 25.0,
                    "humidity": 50.0
                }
            except Exception as e:
                print("Read error:", str(e))
                return None

### 2. Add to Main Script

Update `main.py` to include your new sensor:

    from sensors.temperature.new_sensor import NewSensor
    
    def main():
        # Initialize hardware interface (I2C, ADC, etc.)
        i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        
        # Add your sensor to the sensors dictionary
        sensors = {
            "new_sensor": NewSensor(i2c)
        }

### Common Sensor Types Implementation

#### 1. I2C Sensor

    class I2CSensor(SensorBase):
        def __init__(self, i2c, address, name="I2CSensor"):
            super().__init__(name)
            self.i2c = i2c
            self.address = address
            
        def initialize(self):
            try:
                if self.address not in self.i2c.scan():
                    return False
                self.connected = True
                return True
            except Exception as e:
                print("I2C init error:", str(e))
                return False

#### 2. Analog Sensor

    class AnalogSensor(SensorBase):
        def __init__(self, pin_number, name="AnalogSensor"):
            super().__init__(name)
            self.adc = ADC(Pin(pin_number))
            self.adc.atten(ADC.ATTN_11DB)
            self.adc.width(ADC.WIDTH_12BIT)
            
        def read(self):
            try:
                value = self.adc.read()
                return {"value": value}
            except Exception as e:
                print("Analog read error:", str(e))
                return None

#### 3. Digital Sensor

    class DigitalSensor(SensorBase):
        def __init__(self, pin_number, name="DigitalSensor"):
            super().__init__(name)
            self.pin = Pin(pin_number, Pin.IN)
            
        def read(self):
            try:
                value = self.pin.value()
                return {"state": value}
            except Exception as e:
                print("Digital read error:", str(e))
                return None

## Error Handling

All sensors should:
1. Return `None` when reading fails
2. Properly handle initialization failures
3. Check connection status before reading
4. Use try-except blocks for hardware operations

## Contributing

1. Follow the 4-space indentation style
2. Implement error handling as shown above
3. Update documentation when adding new features
4. Test your sensor implementation thoroughly

## Troubleshooting

Common issues and solutions:

1. Sensor not reading:
    - Check initialization status
    - Verify pin connections
    - Check power supply

2. WiFi connection fails:
    - Verify credentials in config.py
    - Check network availability
    - Reset ESP32 and try again

3. Reading errors:
    - Check sensor connections
    - Verify power supply stability
    - Check for correct pin configuration

## License

MIT License - See LICENSE file for details