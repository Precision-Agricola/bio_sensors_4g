# controller_mqtt/commands.py

import time
from typing import Dict, Any, Optional

def _base_command(command_type: str, sender: str = "controller_mqtt_cli") -> Dict[str, Any]:
    return {
        "timestamp": int(time.time()),
        "sender": sender,
        "command_type": command_type,
        "payload": {}
    }

def create_reset_command() -> Dict[str, Any]:
    return _base_command("reset")

def create_params_command(parameters: Dict[str, Any]) -> Dict[str, Any]:
    cmd = _base_command("params")
    cmd["payload"] = parameters
    return cmd

def create_update_command(version: str, download_url: Optional[str] = None) -> Dict[str, Any]:
    cmd = _base_command("actualizar")
    cmd["payload"] = {"version": version}
    if download_url:
        cmd["payload"]["download_url"] = download_url
    return cmd
