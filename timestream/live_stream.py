import time
import boto3
from datetime import datetime
from config import DEVICE_IDS, DATABASE_NAME, TABLE_NAME, generate_sensor_data

client = boto3.client("timestream-write")
SEND_INTERVAL = 20 * 60  # 20 minutos

FLOAT_FIELDS = [
    "H2S", "NH3", "ph_value",
    "rs485_temperature", "ambient_temperature", "level",
    "pressure", "altitude", "temperature"
]

def convert_row(device_id, data):
    now_ms = int(datetime.now().timestamp() * 1000)
    dimensions = [{"Name": "device_id", "Value": device_id}]
    records = []

    for field in FLOAT_FIELDS:
        val = data.get(field)
        if val is not None:
            records.append({
                "Dimensions": dimensions,
                "MeasureName": field,
                "MeasureValue": str(val),
                "MeasureValueType": "DOUBLE",
                "Time": str(now_ms)
            })

    records.append({
        "Dimensions": dimensions,
        "MeasureName": "aerator_status",
        "MeasureValue": data["aerator_status"],
        "MeasureValueType": "VARCHAR",
        "Time": str(now_ms)
    })

    return records

def live_stream():
    while True:
        now = datetime.now()
        print(f"\n[INFO] Generating real-time data @ {now.isoformat()}")

        for device_id in DEVICE_IDS:
            try:
                data = generate_sensor_data(now, device_id)
                flat_data = {
                    "H2S": data["H2S"],
                    "NH3": data["NH3"],
                    "ph_value": data["Sensor pH"]["ph_value"],
                    "rs485_temperature": data["RS485 Sensor"]["rs485_temperature"],
                    "ambient_temperature": data["RS485 Sensor"]["ambient_temperature"],
                    "level": data["RS485 Sensor"]["level"],
                    "pressure": data["Pressure"]["pressure"],
                    "altitude": data["Pressure"]["altitude"],
                    "temperature": data["Pressure"]["temperature"],
                    "aerator_status": data["aerator_status"]
                }
                records = convert_row(device_id, flat_data)
                client.write_records(
                    DatabaseName=DATABASE_NAME,
                    TableName=TABLE_NAME,
                    Records=records
                )
                print(f"[OK] Sent data for {device_id}")
            except Exception as e:
                print(f"[ERROR] {device_id}: {e}")

        print(f"[WAIT] Sleeping {SEND_INTERVAL} sec...\n")
        time.sleep(SEND_INTERVAL)

if __name__ == "__main__":
    live_stream()
