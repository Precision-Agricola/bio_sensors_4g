# broker/core/aws_forwarding.py
import json
from pico_lte.core import PicoLTE
from machine import Pin
import time

# LED for status indication
led = Pin("LED", Pin.OUT)

# Initialize PicoLTE for AWS IoT Core
try:
    picoLTE = PicoLTE()
    aws_enabled = True
    print("AWS IoT Core connection initialized")
except Exception as e:
    aws_enabled = False
    print(f"Error initializing AWS IoT: {e}")

def send_to_aws(data):
    if not aws_enabled:
        print("AWS IoT Core not initialized, skipping upload")
        return False
    
    try:
        payload_json = {
            "device_id": data.get("device_id", "unknown"),
            "timestamp": data.get("timestamp", 0),
            "sensor_data": data.get("data", {})
        }
        payload = json.dumps(payload_json)
        
        retry_count = 3
        for attempt in range(1, retry_count+1):
            result = picoLTE.aws.publish_message(payload)
            if result["status"] == 0:
                print("Data sent successfully to AWS IoT Core")
                led.toggle()
                return True
            else:
                print(f"Attempt {attempt}: Error sending data to AWS IoT Core: {result}")
                time.sleep(1)
        
        return False
    except Exception as e:
        print(f"ERROR AWS: {e}")
        import sys
        sys.print_exception(e)
        return False

