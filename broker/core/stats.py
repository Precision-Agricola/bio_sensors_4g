# broker/core/stats.py
import time

# Statistics counters
message_count = 0
error_count = 0
aws_success_count = 0
aws_error_count = 0
last_device_seen = {}

def update_statistics(device_id, aws_success):
    """
    Update system statistics
    
    Args:
        device_id: Device ID that sent data
        aws_success: Whether AWS forwarding was successful
    """
    global message_count, aws_success_count, aws_error_count
    
    # Update counters
    message_count += 1
    
    if aws_success:
        aws_success_count += 1
    else:
        aws_error_count += 1
    
    # Update last seen time for device
    last_device_seen[device_id] = time.time()

def get_statistics():
    """
    Get system statistics
    
    Returns:
        dict: Statistics data
    """
    device_status = {}
    
    # Calculate time since last seen for each device
    for device, last_time in last_device_seen.items():
        time_diff = time.time() - last_time
        device_status[device] = {
            "last_seen_seconds_ago": round(time_diff, 1)
        }
    
    return {
        "messages_received": message_count,
        "processing_errors": error_count,
        "aws_successes": aws_success_count,
        "aws_errors": aws_error_count,
        "devices": device_status
    }

def print_stats():
    """Print statistics to console"""
    stats = get_statistics()
    
    print("\n===== MESSAGE STATISTICS =====")
    print(f"Messages received: {stats['messages_received']}")
    print(f"Processing errors: {stats['processing_errors']}")
    print(f"AWS successful sends: {stats['aws_successes']}")
    print(f"AWS send errors: {stats['aws_errors']}")
    
    print("\nLast seen devices:")
    for device, info in stats['devices'].items():
        print(f"  - {device}: {info['last_seen_seconds_ago']} seconds ago")
    
    print("=============================\n")
