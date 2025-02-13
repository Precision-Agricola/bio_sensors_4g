"""Messages module for the sensor package"""
import json
import time

def create_message(sensor_data):
    """
    Build a JSON message containing sensor readings with a timestamp.
    """
    message = {
        "timestamp": time.time(),
        "sensor_data": sensor_data
    }
    return json.dumps(message)
