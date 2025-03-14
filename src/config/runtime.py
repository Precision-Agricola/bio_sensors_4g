AERATOR_PIN_A = 12
AERATOR_PIN_B = 27
BOOT_SELECTOR_PIN = 25
TEST_SELECTOR_PIN = 26

_mqtt_enabled = True 

def get_mqtt_enabled():
    """Returns if MQTT is enabled"""
    return _mqtt_enabled

def set_mqtt_enabled(enabled):
    """Set MQTT enabled status"""
    global _mqtt_enabled
    _mqtt_enabled = bool(enabled)

_runtime_state = {
    "CURRENT_MODE": "EMERGENCY",
    "CURRENT_SPEED": 1
}

def get_mode():
    return _runtime_state["CURRENT_MODE"]

def set_mode(mode):
    _runtime_state["CURRENT_MODE"] = mode

def get_speed():
    return _runtime_state["CURRENT_SPEED"]

def set_speed(speed):
    _runtime_state["CURRENT_SPEED"] = speed
