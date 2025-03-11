"""
Sensor Hardware Test Script
Precisón Agrícola - Test Plan Implementation
March 2025
"""
import time
from machine import SoftI2C, Pin
import json
from system.control.relays import SensorRelay, LoadRelay
import config.runtime as config
from config.config import I2C_SCL_PIN, I2C_SDA_PIN

SENSOR_CONFIG_PATH = "config/sensors.json"



def create_sensor(conf):
    """Create sensor instance from configuration"""
    try:
        from sensors.base import sensor_registry
        
        if "signal" not in conf:
            conf["signal"] = None
        key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
        return sensor_registry.get(key)(**conf)
    except Exception as e:
        print(f"Error creating sensor: {e}")
        return None

def load_sensor_config():
    """Load sensor configurations"""
    try:
        with open(SENSOR_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Config load error:", e)
        return []

def test_relays():
    """Test relay activation (Test d)"""
    print("\n=== TESTING RELAYS ===")
    
    load_relay = LoadRelay(relay_pins=(config.AERATOR_PIN_A, config.AERATOR_PIN_B))
    print("Testing load relays (aerators)...")
    
    for i in range(2):
        print(f"  Testing relay {i}...")
        load_relay.turn_on(i)
        time.sleep(2)
        load_relay.turn_off(i)
        time.sleep(1)
   
    # Test sensor relays (pins 13, 14 - multiplexed)
    sensor_relay = SensorRelay()
    print("Testing sensor relays (multiplexed)...")
    
    print("  Testing relay A...")
    sensor_relay.activate_a()
    time.sleep(2)
    
    print("  Testing relay B...")
    sensor_relay.activate_b()
    time.sleep(2)
    
    print("  Deactivating all relays...")
    sensor_relay.deactivate_all()
    
    print("=== RELAY TEST COMPLETE ===\n")

def test_rtc():
    """Test RTC functionality (Test e)"""
    print("\n=== TESTING RTC ===")
    try:
        from calendar.set_time import set_current_time
        from calendar.get_time import init_rtc, get_current_time
        rtc = init_rtc()
        set_current_time('03/11/2025 00:00')
        rtc_relay = SensorRelay()
        rtc_relay.activate_a()
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
    except Exception as e:
        print(f"RTC TEST ERROR: {e}")
    print("=== RTC TEST COMPLETE ===\n")

def test_analog_sensors():
    """Test analog sensors (Test a)"""
    import sensors.amonia.sen0567
    import sensors.hydrogen_sulfide.sen0568

    print("\n=== TESTING ANALOG SENSORS ===")
    
    sensor_relay = SensorRelay()
    sensor_relay.activate_a()
    time.sleep(2)
    
    sensor_configs = load_sensor_config()
    analog_sensors = [s for s in sensor_configs if s.get("protocol", "").upper() == "ANALOG"]
    
    if not analog_sensors:
        print("No analog sensors configured")
    else:
        for conf in analog_sensors:
            try:
                sensor = create_sensor(conf)
                if sensor:
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
    
    # Power off sensors
    sensor_relay.deactivate_all()
    print("=== ANALOG SENSOR TEST COMPLETE ===\n")

def test_i2c_devices():
    """Test I2C sensors (Tests b & c)"""
    print("\n=== TESTING I2C SENSORS ===")
    import sensors.pressure.bmp3901 
    from utils.micropython_bmpxxx.bmpxxx import BMP390 

    # Power on sensors
    sensor_relay = SensorRelay()
    sensor_relay.activate_a()
    time.sleep(2)
    
    try:
        i2c = SoftI2C(
            scl=Pin(I2C_SCL_PIN),
            sda=Pin(I2C_SDA_PIN))
        detected = i2c.scan()
        print("Detected I2C addresses:", [hex(addr) for addr in detected])
        
        sensor_configs = load_sensor_config()
        i2c_sensors = [s for s in sensor_configs if s.get("protocol", "").upper() == "I2C"]
        
        print("\n-- Address Check --")
        all_ok = True
        for conf in i2c_sensors:
            expected_addr = int(conf['address'], 16)
            if expected_addr in detected:
                print(f"{conf['name']}: OK (0x{expected_addr:02x})")
            else:
                print(f"{conf['name']}: MISSING (0x{expected_addr:02x})")
                all_ok = False
        
        if all_ok and i2c_sensors:
            print("\n-- Sensor Readings --")
            for conf in i2c_sensors:
                try:
                    if conf["name"].lower() == "bmp390": 
                        bmp = BMP390(i2c=i2c, address=int(conf['address'], 16))
                        pressure = bmp.pressure
                        temperature = bmp.temperature
                        altitude = bmp.altitude
                        print(f"{conf['name']}: OK - Pressure: {pressure:.2f} hPa, Temp: {temperature:.2f} °C, Altitude: {altitude:.2f} m")
                    else:
                        sensor = create_sensor(conf)
                        if sensor:
                            reading = sensor.read()
                            status = "OK" if reading is not None else "ERROR"
                            print(f"{conf['name']}: {status} - {reading}")
                except Exception as e:
                    print(f"{conf['name']}: ERROR - {str(e)}")
    except Exception as e:
        print(f"{conf['name']}: ERROR - {str(e)}")
        
    sensor_relay.deactivate_all()
    print("=== I2C TEST COMPLETE ===\n")

def run_hardware_tests():
    """Main test sequence function"""
    print("\n\n=== STARTING HARDWARE TESTS ===")
    
    # Hardware control tests
    test_relays()
    test_rtc()
    
    # Sensor tests
    test_analog_sensors()
    test_i2c_devices()
    
    print("=== ALL TESTS COMPLETED ===")
    return True

if __name__ == "__main__":
    run_hardware_tests()
