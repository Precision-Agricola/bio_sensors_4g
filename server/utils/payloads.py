# server/utils/payloads.py

from config.device_info import DEVICE_ID
from utils.rtc_utils import get_fallback_timestamp


def _base() -> dict:
    return {
        "device_id": DEVICE_ID,
        "system_status": "ok",
        "timestamp": get_fallback_timestamp(),
    }

def build_boot_payload() -> dict:
    msg = _base()
    msg["event"] = "boot"
    return msg

def build_scheduled_reboot_payload() -> dict:
    msg = _base()
    msg["event"] = "scheduled_reboot"
    return msg


def build_command_ack_payload(cmd: str) -> dict:
    msg = _base()
    msg["event"] = "command_ack"
    msg["command_type"] = cmd
    return msg
