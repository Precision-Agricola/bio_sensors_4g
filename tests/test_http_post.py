import network, time
from routines.sensor_routine import SensorRoutine

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"

def connect_and_retry():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        for _ in range(10):
            if wlan.isconnected():
                break
            time.sleep(1)

    if wlan.isconnected():
        mac = wlan.config('mac')[-3:]
        device_id = "server_" + ''.join('{:02X}'.format(b) for b in mac)
        print("Connected:", wlan.ifconfig()[0])
        print("Device ID:", device_id)
        SensorRoutine().retry_pending_data()
    else:
        print("Connection failed.")

connect_and_retry()
