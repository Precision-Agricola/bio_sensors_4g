"""Handling the commands for sensing data request"""

import json
import time
from core.utils import debug_print

pending_commands = []

def send_command(device_id, command, params=None):
    if params is None:
        params = {}
    cmd_data = {
        "command": command,
        "timestamp": time.time(),
        "params": params,
        "command_id": f"cmd_{int(time.time())}_{device_id}"
    }
    topic = f"command/{device_id}" if device_id != "all" else "command/all"
    pending_commands.append({
        "topic": topic,
        "payload": json.dumps(cmd_data),
        "timestamp": time.time()
    })
    debug_print(f"Command saved {topic}: {command}")

def request_reading(device_id="all"):
    send_command(device_id, "READ_NOW")
