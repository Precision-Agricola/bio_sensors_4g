# upload_history.py (pre-version con salida CSV)

import csv
from datetime import datetime, timedelta
from pathlib import Path
from config import DEVICE_IDS, generate_sensor_data

OUTPUT_DIR = Path("simulated_data")
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"Output directory: {OUTPUT_DIR.resolve()}")

def flatten_data(device_id, timestamp, data):
    flat = {
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "H2S": data["H2S"],
        "NH3": data["NH3"],
        "ph_value": data["Sensor pH"]["ph_value"],
        "aerator_status": data["aerator_status"]
    }

    rs485 = data["RS485 Sensor"]
    flat.update({
        "rs485_temperature": rs485["rs485_temperature"],
        "ambient_temperature": rs485["ambient_temperature"],
        "level": rs485["level"]
    })

    pressure = data["Pressure"]
    flat.update({
        "pressure": pressure["pressure"],
        "altitude": pressure["altitude"],
        "temperature": pressure["temperature"]
    })

    return flat

def write_device_csv(device_id, rows):
    filepath = OUTPUT_DIR / f"data_{device_id}.csv"
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {filepath} with {len(rows)} rows")

def generate_history_csv(start_time, end_time):
    print(f"Generating data from {start_time} to {end_time}")
    current_time = start_time
    device_data = {dev: [] for dev in DEVICE_IDS}

    steps = 0
    while current_time <= end_time:
        for device_id in DEVICE_IDS:
            data = generate_sensor_data(current_time)
            flat = flatten_data(device_id, current_time, data)
            device_data[device_id].append(flat)
        current_time += timedelta(hours=1)
        steps += 1
        if steps % 24 == 0:
            print(f"...processed {steps} hourly steps")

    for dev_id, rows in device_data.items():
        write_device_csv(dev_id, rows)

if __name__ == "__main__":
    start = datetime(2025, 4, 11, 18, 18)
    end = datetime.now()
    generate_history_csv(start, end)
