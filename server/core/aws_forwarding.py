# broker/core/aws_forwarding.py

import json
from pico_lte.core import PicoLTE
from machine import Pin
import time
from utils.logger import log_message
from config.device_info import DEVICE_ID

# LED for status indication
led = Pin("LED", Pin.OUT)

# Initialize PicoLTE for AWS IoT Core
try:
    picoLTE = PicoLTE()
    aws_enabled = True
    log_message("AWS IoT Core connection initialized")
except Exception as e:
    aws_enabled = False
    log_message(f"Error initializing AWS IoT: {e}")

def send_to_aws(data):
    if not aws_enabled:
        log_message("AWS IoT Core not initialized, skipping upload")
        return False
    
    try:
        payload_json = {}

        for k, v in data.items():
            payload_json[k] = v

        payload_json["device_id"] = DEVICE_ID # Server ID & client ID in payload

        payload = json.dumps(payload_json)
        retry_count = 3
        for attempt in range(1, retry_count+1):
            result = picoLTE.aws.publish_message(payload)
            if result["status"] == 0:
                log_message("Data sent successfully to AWS IoT Core")
                led.toggle()
                return True
            else:
                log_message(f"Attempt {attempt}: Error sending data to AWS IoT Core: {result}")
                time.sleep(1)
        
        return False
    except Exception as e:
        log_message(f"ERROR AWS: {e}")
        import sys
        sys.log_message_exception(e)
        return False
