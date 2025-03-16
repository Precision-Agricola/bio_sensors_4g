"""General Utilities"""

# core/utils.py
from machine import Pin
import json, time

DEBUG_MODE = True
led = Pin("LED", Pin.OUT)

def debug_print(msg, data=None, force=False):
    if DEBUG_MODE or force:
        print(msg, data if data else "")

def handle_received_payload(payload, stats, led, aws_publish_func):
    message = payload.decode()
    data = json.loads(message)
    stats["messages"] += 1
    debug_print(f"Mensaje #{stats['messages']} de {data.get('device_id')}")
    aws_publish_func(data, stats)
    led.toggle()

def print_stats(stats, last_seen):
    print(f"Mensajes: {stats['messages']} Errores: {stats['errors']} AWS OK: {stats['aws_success']} AWS Err: {stats['aws_error']}")
    for device, timestamp in last_seen.items():
        print(f"{device}: hace {time.time() - timestamp:.1f}s")
