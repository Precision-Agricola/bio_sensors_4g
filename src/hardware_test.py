"""
Sensor Hardware Test Script
Precisón Agrícola - Test Plan Implementation
"""

import time
from machine import Pin, I2C
import json

# Reuse sensor creation logic from main code
from sensors.base import sensor_registry

# Configuration paths and settings
SENSOR_CONFIG_PATH = "config/sensors.json"
RELAY_PINS_UNDER_TEST = [12, 13, 14, 27]
I2C_BUS_ID = 0  # Update based on actual hardware configuration

def create_sensor(conf):
    """Replicated from main code for sensor creation"""
    if "signal" not in conf:
        conf["signal"] = None
    key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
    return sensor_registry.get(key)(**conf)

def load_sensor_config():
    """Load sensor configurations"""
    try:
        with open(SENSOR_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Config load error:", e)
        return []

def power_sensors(activate=True):
    """Control power relays for sensors"""
    relay13 = Pin(13, Pin.OUT)
    relay14 = Pin(14, Pin.OUT)
    relay13.value(1 if activate else 0)
    relay14.value(1 if activate else 0)
    if activate:
        time.sleep(2)  # Stabilization time

# --------------------------
# Test Implementations
# --------------------------

def test_relays():
    """Test relay activation (Test d)"""
    print("\n=== TESTING RELAYS ===")
    for pin_num in RELAY_PINS_UNDER_TEST:
        try:
            pin = Pin(pin_num, Pin.OUT)
            print(f"Testing GPIO {pin_num}...")
            
            pin.value(1)
            print("  Activated - waiting 2s")
            time.sleep(2)
            
            pin.value(0)
            print("  Deactivated - waiting 1s")
            time.sleep(1)
            
        except Exception as e:
            print(f"ERROR on GPIO {pin_num}: {str(e)}")
    print("=== RELAY TEST COMPLETE ===\n")

def test_rtc():
    """Test RTC functionality (Test e)"""
    print("\n=== TESTING RTC ===")
    from calendar.get_time import init_rtc, get_current_time
    
    rtc = init_rtc()
    initial_time = get_current_time(rtc)
    print("Initial RTC time:", f"{initial_time[3]:02}:{initial_time[4]:02}:{initial_time[5]:02}")
    
    time.sleep(5)
    
    new_time = get_current_time(rtc)
    print("New RTC time:", f"{new_time[3]:02}:{new_time[4]:02}:{new_time[5]:02}")
    
    time_diff = (new_time[5] - initial_time[5]) % 60
    if 4 <= time_diff <= 6:  # Allow 1s margin
        print("RTC OK - Time progressing correctly")
    else:
        print(f"RTC ERROR - Time difference: {time_diff}s")
    print("=== RTC TEST COMPLETE ===\n")

def test_analog_sensors():
    """Test analog sensors (Test a)"""
    print("\n=== TESTING ANALOG SENSORS ===")
    power_sensors(True)
    
    sensor_configs = load_sensor_config()
    analog_sensors = [s for s in sensor_configs if s.get("protocol", "").upper() == "ANALOG"]
    
    if not analog_sensors:
        print("No analog sensors configured")
        return
    
    for conf in analog_sensors:
        try:
            sensor = create_sensor(conf)
            reading = sensor.read()
            print(f"{conf['name']} ({conf['model']}):", end=" ")
            
            if reading is None:
                print("ERROR - No reading")
            elif reading == 0:
                print("WARNING - Zero value")
            else:
                print(f"OK - Value: {reading}")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    power_sensors(False)
    print("=== ANALOG SENSOR TEST COMPLETE ===\n")

def test_i2c_devices():
    """Test I2C sensors (Tests b & c)"""
    print("\n=== TESTING I2C SENSORS ===")
    power_sensors(True)
    
    try:
        # Initialize I2C bus
        i2c = I2C(I2C_BUS_ID)
        detected = i2c.scan()
        print("Detected I2C addresses:", [hex(addr) for addr in detected])
        
        # Get configured I2C sensors
        sensor_configs = load_sensor_config()
        i2c_sensors = [s for s in sensor_configs if s.get("protocol", "").upper() == "I2C"]
        
        # Test b: Address verification
        print("\n-- Address Check --")
        all_ok = True
        for conf in i2c_sensors:
            expected_addr = int(conf['address'], 16)
            if expected_addr in detected:
                print(f"{conf['name']}: OK (0x{expected_addr:02x})")
            else:
                print(f"{conf['name']}: MISSING (0x{expected_addr:02x})")
                all_ok = False
        
        # Test c: Sensor reading
        if all_ok:
            print("\n-- Sensor Readings --")
            for conf in i2c_sensors:
                try:
                    sensor = create_sensor(conf)
                    reading = sensor.read()
                    status = "OK" if reading is not None else "ERROR"
                    print(f"{conf['name']}: {status} - {reading}")
                except Exception as e:
                    print(f"{conf['name']}: ERROR - {str(e)}")
        else:
            print("\nSkipping readings due to missing devices")
            
    except Exception as e:
        print(f"I2C COMMUNICATION ERROR: {str(e)}")
    
    power_sensors(False)
    print("=== I2C TEST COMPLETE ===\n")

# --------------------------
# Main Test Sequence
# --------------------------

if __name__ == "__main__":
    print("\n\n=== STARTING HARDWARE TESTS ===")
    
    # Hardware control tests
    test_relays()
    test_rtc()
    
    # Sensor tests (require powered sensors)
    test_analog_sensors()
    test_i2c_devices()
    
    print("=== ALL TESTS COMPLETED ===")
