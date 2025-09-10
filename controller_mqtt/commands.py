# controller_mqtt/commands.py

import time
from typing import Dict, Any

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

def create_fetch_update_command(details_url: str) -> Dict[str, Any]:
    """Crea el payload para el comando disparador 'fetch_update'."""
    cmd = _base_command("fetch_update")
    cmd["payload"]["details_url"] = details_url
    return cmd

def create_server_reboot_command() -> Dict[str, Any]:
    """Crea el payload para el comando de reinicio del servidor."""
    cmd = _base_command("reset")
    return cmd

def create_update_command(target: str, url: str) -> Dict[str, Any]:
    """Crea el payload para el comando de actualización simplificado."""
    cmd = _base_command("update")
    cmd["payload"] = {
        "target": target,
        "url": url
    }
    return cmd
