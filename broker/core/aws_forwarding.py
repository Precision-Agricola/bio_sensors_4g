import json
import os
import time
import machine
from pico_lte.core import PicoLTE
from machine import Pin

# LED for status indication
led = Pin("LED", Pin.OUT)

DATA_DIR = "/data"
try:
    os.mkdir(DATA_DIR)
except OSError:
    pass

try:
    picoLTE = PicoLTE()
    aws_enabled = True
    print("AWS IoT Core connection initialized")
except Exception as e:
    aws_enabled = False
    print(f"Error initializing AWS IoT: {e}")

aws_failures = 0  # global counter for AWS failures

def send_to_aws(data):
    global aws_enabled, aws_failures

    if not aws_enabled:
        print("AWS IoT Core not initialized, skipping upload")
        return False

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
            aws_failures = 0  # Reset counter on success
            return True
        else:
            print(f"Attempt {attempt}: Error sending data to AWS IoT Core: {result}")
            time.sleep(1)

    # AWS failed after retries, increment failure counter
    aws_failures += 1
    save_failed_data(payload_json)

    if aws_failures >= 5:
        print("AWS failed 5 times consecutively. Restarting system.")
        time.sleep(2)
        machine.reset()  # Restart device explicitly

    return False

def save_failed_data(payload):
    try:
        filename = f"{DATA_DIR}/sensor_{int(payload['timestamp'])}.json"
        with open(filename, 'w') as f:
            json.dump(payload, f)
        print(f"Saved unsent data to {filename}")
    except Exception as e:
        print("Failed to save pending data:", e)

def retry_pending_data():
    global aws_failures
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.startswith("sensor_")]
        files.sort()  # send oldest first
        for file in files:
            path = f"{DATA_DIR}/{file}"
            with open(path, 'r') as f:
                payload = json.load(f)
            print(f"Retrying to send stored data: {file}")
            if send_to_aws(payload):
                os.remove(path)
                print(f"Successfully sent and removed {file}")
            else:
                print(f"Failed again, stopping retry at {file}")
                break
        aws_failures = 0  # reset counter if pending data sent successfully
    except Exception as e:
        print("Error during retry of pending data:", e)

