from config.device_info import DEVICE_ID
from utils.rtc_utils import get_fallback_timestamp


def _base() -> dict:
    return {
        "device_id": DEVICE_ID,
        "system_status": "ok",
        "timestamp": get_fallback_timestamp(),
    }

def build_boot_payload() -> dict:
    payload = _base()
    payload["event"] = "boot"
    return payload

def build_scheduled_reboot_payload() -> dict:
    payload = _base()
    payload["event"] = "scheduled_reboot"
    return payload
