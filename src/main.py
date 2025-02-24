"""Sensor reading and data transmission code

Precisón Agrícola
Investigation and Development Department

@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025

"""
import time
import json
from machine import Pin, Timer
from calendar.get_time import init_rtc, get_current_time
import sensors.amonia.sen0567 
import sensors.hydrogen_sulfide.sen0568
import sensors.pressure.bmp3901

# Relay configuration
relay1 = Pin(13, Pin.OUT)
relay2 = Pin(14, Pin.OUT)

def activate_relays():
    """Activate both relays and wait for stabilization."""
    relay1.value(1)
    relay2.value(1)
    time.sleep(2)  # Allow time for stabilization

def deactivate_relays():
    """Deactivate both relays."""
    relay1.value(0)
    relay2.value(0)

def load_sensor_config(path="config/sensors.json"):
    """Load sensor configurations from a JSON file.

    Args:
        path (str): Path to the sensor configuration file. Defaults to 'config/sensors.json'.

    Returns:
        list: List of sensor configurations, or empty list if loading fails.
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sensor config:", e)
        return []

def create_sensor(conf):
    """Create a sensor instance based on its configuration.

    Args:
        conf (dict): Configuration dictionary for the sensor.

    Returns:
        object: Sensor instance if registered, None otherwise.
    """
    from sensors.base import sensor_registry  # Lazy import to avoid circular issues
    if "signal" not in conf:
        conf["signal"] = None
    key = (conf["model"].strip().upper(), conf["protocol"].strip().upper())
    sensor_cls = sensor_registry.get(key)
    if sensor_cls:
        return sensor_cls(**conf)
    print(f"Unregistered sensor: {key}")
    return None

def test_sensors(sensor_configs):
    """Test all sensors and return their status and readings.

    Args:
        sensor_configs (list): List of sensor configuration dictionaries.

    Returns:
        dict: Sensor status with names as keys and status/reading as values.
    """
    sensor_status = {}
    for conf in sensor_configs:
        sensor = create_sensor(conf)
        if sensor:
            reading = sensor.read()
            sensor_status[conf["name"]] = {
                "status": "OK" if reading is not None else "Error",
                "reading": reading
            }
        else:
            sensor_status[conf["name"]] = {"status": "Unregistered", "reading": None}
    return sensor_status

def prepare_payload(sensor_status):
    """Prepare a payload with timestamp and sensor status.

    Args:
        sensor_status (dict): Dictionary of sensor statuses.

    Returns:
        dict: Payload with timestamp and sensor data.
    """
    return {
        "timestamp": time.time(),
        "sensors": sensor_status
    }

def sensor_routine():
    """Execute the sensor reading routine and send data via WiFi with a random delay."""
    from local_network.wifi import send_data
    import random
    sensor_configs = load_sensor_config()
    if not sensor_configs:
        print("No sensor configurations found!")
        return
    activate_relays()
    status = test_sensors(sensor_configs)
    deactivate_relays()
    payload = prepare_payload(status)
    json_payload = json.dumps(payload)
    print("Payload:", payload)
    print("JSON Payload:", json_payload)
    time.sleep(random.uniform(0, 5))
    send_data(json_payload)
    schedule_next_run()  # Reschedule after completion

def schedule_next_run():
    """Schedule the next sensor routine execution at the 10th second of the next minute."""
    y, mo, d, h, m, s = get_current_time(rtc)
    seconds_until_next = (60 - s + 10) % 60  # Time until next minute's 10th second
    if seconds_until_next == 0:
        seconds_until_next = 60  # Full minute if exactly on time
    timer.init(period=seconds_until_next * 1000, mode=Timer.ONE_SHOT, callback=lambda t: sensor_routine())

def check_time(timer):
    """Check current time and trigger sensor routine at the 10th second.

    Args:
        timer: Timer object (unused, required by callback).
    """
    y, mo, d, h, m, s = get_current_time(rtc)
    if s == 10:
        print(f"Starting routine at {h}:{m}:{s}")
        sensor_routine()

# Initialize RTC
rtc = init_rtc()
timer = Timer(0)
schedule_next_run()

# Main loop
while True:
    time.sleep(1)
