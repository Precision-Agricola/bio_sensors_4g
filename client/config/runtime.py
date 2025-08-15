#client/config/runtime.py

import ujson as json

AERATOR_PIN_A = 33
AERATOR_PIN_B = 4
BOOT_SELECTOR_PIN = 25
TEST_SELECTOR_PIN = 26

CONFIG_PATH = "config/config_persist.json"

_runtime_state = {
    "CURRENT_MODE": "UNKNOWN",
    "CURRENT_SPEED": 1,
    "REBOOT_REQUESTED": False
}

# Estado de ejecución
def get_mode(): return _runtime_state["CURRENT_MODE"]
def set_mode(mode): _runtime_state["CURRENT_MODE"] = mode
def get_speed(): return _runtime_state["CURRENT_SPEED"]
def set_speed(speed): _runtime_state["CURRENT_SPEED"] = speed

# Config persistente
def _load_persisted_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except:
        return {}

_persisted = _load_persisted_config()

def get_cycle_duration():
    return _persisted.get("cycle_hours", 6)

def get_duty_cycle():
    return _persisted.get("duty_cycle", 0.5)

def get_pump_interval():
    return _persisted.get("pump_config", {}).get("interval_min", 180)

def get_pump_duration():
    return _persisted.get("pump_config", {}).get("duration_min", 10)

def save_config(cycle_hours=None, duty_cycle=None, pump_interval=None, pump_duration=None):
    if cycle_hours is not None:
        _persisted["cycle_hours"] = cycle_hours
    if duty_cycle is not None:
        _persisted["duty_cycle"] = duty_cycle
    
    if pump_interval is not None or pump_duration is not None:
        if "pump_config" not in _persisted:
            _persisted["pump_config"] = {}
        if pump_interval is not None:
            _persisted["pump_config"]["interval_min"] = pump_interval
        if pump_duration is not None:
            _persisted["pump_config"]["duration_min"] = pump_duration
            
    with open(CONFIG_PATH, "w") as f:
        json.dump(_persisted, f)
