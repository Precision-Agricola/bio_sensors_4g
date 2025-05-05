# load_csv_to_timestream.py

import csv
import boto3
from pathlib import Path
from datetime import datetime
from config import DATABASE_NAME, TABLE_NAME

client = boto3.client("timestream-write")
CSV_DIR = Path("simulated_data")

FLOAT_FIELDS = [
    "H2S", "NH3", "ph_value",
    "rs485_temperature", "ambient_temperature", "level",
    "pressure", "altitude", "temperature"
]

def convert_row(row):
    dimensions = [{"Name": "device_id", "Value": row["device_id"]}]
    time_ms = int(datetime.fromisoformat(row["timestamp"]).timestamp() * 1000)
    records = []

    for field in FLOAT_FIELDS:
        val = row[field]
        if val:
            records.append({
                "Dimensions": dimensions,
                "MeasureName": field,
                "MeasureValue": val,
                "MeasureValueType": "DOUBLE",
                "Time": str(time_ms)
            })

    records.append({
        "Dimensions": dimensions,
        "MeasureName": "aerator_status",
        "MeasureValue": row["aerator_status"],
        "MeasureValueType": "VARCHAR",
        "Time": str(time_ms)
    })

    return records

def load_csv_file(file_path):
    print(f"Loading {file_path.name}...")
    with open(file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                records = convert_row(row)
                client.write_records(
                    DatabaseName=DATABASE_NAME,
                    TableName=TABLE_NAME,
                    Records=records
                )
            except Exception as e:
                print(f"Failed to write row {row['timestamp']} for {row['device_id']}: {e}")

def main():
    for csv_file in CSV_DIR.glob("data_*.csv"):
        load_csv_file(csv_file)

if __name__ == "__main__":
    main()
