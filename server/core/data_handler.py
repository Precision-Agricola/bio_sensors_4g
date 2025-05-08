# broker/core/data_handler.py
import json
import time
from core.aws_forwarding import send_to_aws
from core.stats import update_statistics
from utils.logger import log_message

# Storage for received data and commands
received_data = []
pending_commands = {}

def process_sensor_data(data):
    """
    Process sensor data received from devices
    
    Args:
        data: JSON data from sensor device
        
    Returns:
        bool: Success status
    """
    # Add timestamp if not present
    if 'timestamp' not in data:
        data['timestamp'] = time.time()
    
    # Store data (limited to last 100 entries)
    if len(received_data) >= 100:
        received_data.pop(0)
    received_data.append(data)
    
    # Extract device ID
    device_id = data.get('device_id', 'unknown')
    
    # log_message data summary
    log_message("\n" + "=" * 40)
    log_message(f"DATA RECEIVED FROM: {device_id}")
    log_message(f"Timestamp: {data.get('timestamp')}")
    
    # Display sensor data
    if 'data' in data:
        log_message("\nSensor readings:")
        for sensor_name, sensor_value in data['data'].items():
            if isinstance(sensor_value, dict):
                log_message(f"  - {sensor_name}: {sensor_value}")
            else:
                log_message(f"  - {sensor_name}: {sensor_value}")
    log_message("=" * 40 + "\n")
    
    # Forward to AWS IoT
    aws_result = send_to_aws(data)
    
    # Update statistics
    update_statistics(device_id, aws_result)
    
    return True

def queue_command(device_id, command, params=None):
    """
    Queue a command for a device
    
    Args:
        device_id: Target device ID or "all" for all devices
        command: Command name
        params: Command parameters (optional)
        
    Returns:
        str: Command ID
    """
    if params is None:
        params = {}
    
    cmd_id = f"cmd_{int(time.time())}_{device_id}"
    
    # Create command data
    cmd_data = {
        "command": command,
        "timestamp": time.time(),
        "params": params,
        "command_id": cmd_id
    }
    
    # Initialize device entry if doesn't exist
    if device_id not in pending_commands:
        pending_commands[device_id] = []
    
    # Add command to queue
    pending_commands[device_id].append(cmd_data)
    
    # Also add to "all" queue if this is a device-specific command
    if device_id != "all":
        if "all" not in pending_commands:
            pending_commands["all"] = []
        pending_commands["all"].append(cmd_data)
    
    log_message(f"Command queued for {device_id}: {command}")
    return cmd_id

def get_pending_commands(device_id):
    """
    Get pending commands for a device
    
    Args:
        device_id: Device ID to fetch commands for
        
    Returns:
        list: List of command objects
    """
    # Get device-specific commands
    commands = pending_commands.get(device_id, [])[:]
    
    # Also get "all" commands if this is a specific device
    if device_id != "all":
        all_commands = pending_commands.get("all", [])[:]
        commands.extend(all_commands)
    
    # Clear the pending commands for this device
    if device_id in pending_commands:
        pending_commands[device_id] = []
    
    # Mark timestamp when commands were retrieved
    for cmd in commands:
        cmd["retrieved_at"] = time.time()
    
    return commands
