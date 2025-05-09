import time
import boto3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from config import DEVICE_IDS, DATABASE_NAME, TABLE_NAME, generate_sensor_data

local_tz = ZoneInfo("America/Mazatlan")
CYCLE_START_UTC = datetime(2025, 5, 8, 21, 13, tzinfo=timezone.utc)

client = boto3.client("timestream-write")
SEND_INTERVAL = 60 * 60  # 20 minutos
SEND = True # ← cambiar a True cuando quieras enviar

FLOAT_FIELDS = [
    "H2S", "NH3", "ph_value",
    "rs485_temperature", "ambient_temperature", "level",
    "pressure", "altitude", "temperature"
]

def get_cycle_id(timestamp):
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    delta_min = int((timestamp.astimezone(timezone.utc) - CYCLE_START_UTC).total_seconds() // 60)
    return delta_min // 180

def convert_row(device_id, data, cycle_id, now_ms):
    dimensions = [{"Name": "device_id", "Value": device_id}]
    records = []

    for field in FLOAT_FIELDS:
        if field in data:
            val = data[field]
        elif field in data.get("Sensor P H", {}):
            val = data["Sensor P H"][field]
        elif field in data.get("Sensor pH", {}):
            val = data["Sensor pH"][field]
        elif field in data.get("RS485 Sensor", {}):
            val = data["RS485 Sensor"][field]
        elif field in data.get("Pressure", {}):
            val = data["Pressure"][field]
        else:
            val = None

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

    records.append({
        "Dimensions": dimensions,
        "MeasureName": "cycle_id",
        "MeasureValue": str(cycle_id),
        "MeasureValueType": "BIGINT",
        "Time": str(now_ms)
    })

    return records


def live_stream():
    while True:
        now = datetime.now(timezone.utc).astimezone(local_tz)
        now_ms = int(now.astimezone(timezone.utc).timestamp() * 1000)
        cycle_id = get_cycle_id(now)
        cycle_phase = "ON" if (cycle_id % 2 == 0) else "OFF"

        print("="*60)
        print(f"[DEBUG] Hora local Mazatlán: {now.isoformat()}")
        print(f"[DEBUG] Hora UTC: {now.astimezone(timezone.utc).isoformat()}")
        print(f"[DEBUG] now_ms (UTC): {now_ms}")
        print(f"[DEBUG] Ciclo actual: {cycle_id}")
        print(f"[DEBUG] Fase: {cycle_phase}")
        print("="*60)

        for device_id in DEVICE_IDS:
            try:
                data = generate_sensor_data(now, device_id, cycle_id=cycle_id)
                records = convert_row(device_id, data, cycle_id, now_ms)

                if SEND:
                    client.write_records(
                        DatabaseName=DATABASE_NAME,
                        TableName=TABLE_NAME,
                        Records=records
                    )
                    print(f"[OK] Sent data for {device_id}")
                else:
                    print(f"[SKIPPED] Data not sent for {device_id}")

            except Exception as e:
                print(f"[ERROR] {device_id}: {repr(e)}")

        print(f"[WAIT] Sleeping {SEND_INTERVAL} sec...\n")
        time.sleep(SEND_INTERVAL)

if __name__ == "__main__":
    try:
        live_stream()
    except KeyboardInterrupt:
        print("\n[INFO] Exiting...")
    except Exception as e:
        print(f"[ERROR] {repr(e)}")
