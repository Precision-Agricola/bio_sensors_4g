from utils.logger import log_message

AERATOR_PIN_A = 12
AERATOR_PIN_B = 27
BOOT_SELECTOR_PIN = 25
TEST_SELECTOR_PIN = 26

_runtime_state = {
    "CURRENT_MODE": "UNKNOWN",
    "CURRENT_SPEED": 1,
    "REBOOT_REQUESTED": False
}

# --- Funciones Get/Set Modo y Velocidad (existentes) ---
def get_mode():
    return _runtime_state["CURRENT_MODE"]

def set_mode(mode):
    _runtime_state["CURRENT_MODE"] = mode

def get_speed():
    return _runtime_state["CURRENT_SPEED"]

def set_speed(speed):
    _runtime_state["CURRENT_SPEED"] = speed

# --- Funciones para gestionar la solicitud de reinicio (nuevas) ---
def request_reboot():
    """Marca la bandera para solicitar un reinicio coordinado."""
    log_message("INFO: Reboot request flag set.")
    _runtime_state["REBOOT_REQUESTED"] = True

def clear_reboot_request():
    """Limpia la bandera de solicitud de reinicio (ej. si WiFi se recupera)."""
    if _runtime_state["REBOOT_REQUESTED"]:
        log_message("INFO: Clearing reboot request flag.")
        _runtime_state["REBOOT_REQUESTED"] = False

def is_reboot_requested():
    """Verifica si se ha solicitado un reinicio."""
    return _runtime_state["REBOOT_REQUESTED"]
