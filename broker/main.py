"""MQTT Broker para Raspberry Pi Pico W con integración AWS IoT Core

Este script actúa como broker MQTT local y retransmite los datos a AWS IoT Core.
Recibe datos de sensores a través del punto de acceso local y los reenvía a AWS.
"""

# broker/main.py (new version)
from microdot import Microdot
from core.wifi import setup_access_point
from core.utils import print_stats, led
import time, gc

SSID = "PrecisionAgricola"
PASSWORD = "ag2025pass"
app = Microdot()
received_data = []
pending_commands = {}

@app.route('/data', methods=['POST'])
def receive_data(request):
    data = request.json
    received_data.append(data)
    led.toggle()
    return {'status': 'received'}, 200

@app.route('/commands', methods=['GET'])
def get_commands(request):
    device_id = request.args.get('device_id')
    commands = pending_commands.get(device_id, [])
    pending_commands[device_id] = []
    return {'commands': commands}, 200

def main():
    setup_access_point(SSID, PASSWORD)
    print("Starting HTTP server...")
    app.run(port=80)

if __name__ == "__main__":
    main()
