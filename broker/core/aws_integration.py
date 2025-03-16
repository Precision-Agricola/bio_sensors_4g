"""AWS Domestic Integration"""

# core/aws_integration.py
import json
import time
from pico_lte.core import PicoLTE
from core.utils import debug_print

picoLTE = PicoLTE()

def publish_to_aws(data, stats):
    payload_json = {
        "device_id": data.get("device_id", "unknown"),
        "timestamp": data.get("timestamp", time.time()),
        "sensor_data": data.get("data", {})
    }
    payload = json.dumps(payload_json)
    result = picoLTE.aws.publish_message(payload)
    if result["status"] == 0:
        stats["aws_success"] += 1
        debug_print("Enviado correctamente a AWS", force=True)
        return True
    else:
        stats["aws_error"] += 1
        debug_print("Error enviando a AWS:", result, force=True)
        return False
