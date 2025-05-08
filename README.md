# ESP32 Sensor Data Collection System

A modular MicroPython-based system for collecting sensor data and transmitting it via WiFi.

## Project Structure

    project_root/
        ├── docs/                  # Documentation
        ├── src/
        │   ├── config/
        │   │   ├── device_config.json
        │   │   └── sensors.json
        │   ├── main.py            # Main script
        │   ├── network/           # Network communication
        │   └── sensors/           # Sensor implementations
        │       ├── base.py        # Base sensor class & registry
        │       └── ...            # Other sensor modules (temperature, pressure, etc.)
        └── tests/                 # Unit tests

## Bioreactor ID
 - bioreactor 1: ESP32_3002EC
 - bioreactor 2: ESP32_5DAEC4
## Installation

1. Flash MicroPython to your ESP32:

        esptool.py --port /dev/ttyUSB0 erase_flash
        esptool.py --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-{version}.bin

2. Upload project files:

        ampy --port /dev/ttyUSB0 put src/

3. Update `src/config/device_config.json` with your WiFi and server details.

## Configuration

Edit `src/config/device_config.json`:

        {
            "wifi": {
                "ssid": "YourWiFiSSID",
                "password": "YourWiFiPassword"
            },
            "server_ip": "192.168.1.100",
            "port": 5000
        }

Edit `src/config/sensors.json` to define your sensors:

        {
            "sensors": [
                {
                    "name": "Pressure Sensor",
                    "model": "BMP390L",
                    "protocol": "I2C",
                    "vin": 3.3,
                    "signal": "I2C",
                    "address": 119,
                    "bus": 0
                },
                {
                    "name": "NH3 Sensor",
                    "model": "SEN0567",
                    "protocol": "Analog",
                    "vin": 3.3,
                    "signal": "Analog",
                    "pin": 34,
                    "window_size": 5
                }
            ]
        }

## Adding New Sensors

1. **Create a Sensor Class**

   In the appropriate folder (e.g., `src/sensors/new_type/`), create a new file (e.g., `your_sensor.py`) and implement your sensor using the base class and registration decorator:

        from sensors.base import Sensor, register_sensor

        @register_sensor("YOUR_MODEL", "YOUR_PROTOCOL")
        class YourSensor(Sensor):
            def _init_hardware(self):
                # Initialize sensor hardware here
                super()._init_hardware()

            def _read_implementation(self):
                # Return sensor reading as a dict
                return {"value": 42}

2. **Update Sensor Configuration**

   Add your sensor's configuration to `src/config/sensors.json`:

        {
            "name": "Your Sensor Name",
            "model": "YOUR_MODEL",
            "protocol": "YOUR_PROTOCOL",
            "vin": 3.3,
            "signal": "Analog",
            "pin": 33,
            "additional_param": "value"
        }

   The system auto-loads and registers your sensor based on this config.

## Running the System

With proper configuration, simply run `main.py` on your ESP32 to start sensor readings and data transmission.

## Testing

Run unit tests from the `tests/` folder:

        python -m unittest discover tests

## License

MIT License
