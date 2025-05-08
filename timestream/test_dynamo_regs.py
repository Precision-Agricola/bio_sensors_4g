# test_dynamo_scan.py
import boto3
from decimal import Decimal
import os
from datetime import datetime, timezone

def format_timestamp(ms):
    try:
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).isoformat()
    except Exception as e:
        return f"[ERROR] {e}"

def _convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

TABLE_NAME = os.getenv("IOT_DYNAMO_TABLE", "SensorDataTable")
REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def scan_and_sort_by_insertion(device_id, limit=5):
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("device_id").eq(device_id)
    )
    items = response.get("Items", [])
    items.sort(key=lambda x: float(x.get("payload", x).get("insertion_time", 0)), reverse=True)
    return [_convert_decimals(i) for i in items[:limit]]

# Prueba
if __name__ == "__main__":
    items = scan_and_sort_by_insertion("ESP32_5DAEC4", limit=3)
    for i, item in enumerate(items):
        data = item.get("payload", item)
        print(f"[{i}] insertion_time: {format_timestamp(data.get('insertion_time'))}, data: {data}")

