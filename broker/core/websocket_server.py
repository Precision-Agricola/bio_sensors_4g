import uasyncio as asyncio
import os
import time
import random
import machine
from microdot import Microdot, Response, send_file
from websocket import with_websocket
from core.aws_forwarding import send_to_aws

# Configure watchdog with maximum (8 seconds)
wdt = machine.WDT(timeout=8000)
last_heartbeat = time.ticks_ms()  # Global timestamp

Response.default_content_type = 'text/html'

app = Microdot()
clients = {}

async def watchdog_feeder():
    global last_heartbeat
    while True:
        if time.ticks_diff(time.ticks_ms(), last_heartbeat) < 5 * 60 * 1000:
            wdt.feed()
        else:
            log_watchdog_event()
            break
        await asyncio.sleep(1)

def log_watchdog_event():
    # Create a timestamp string.
    t = time.localtime()
    ts = "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
    # Count files in /data.
    try:
        file_count = len(os.listdir('/data'))
    except Exception as e:
        file_count = "error"
    # Log the event.
    with open('/log.txt', 'a') as f:
        f.write("{} - Watchdog triggered. /data file count: {}\n".format(ts, file_count))
    print("No PONG for  minutes: letting watchdog reset the system.")


@app.route('/')
async def index(request):
    # Simple page that could later load your WebSocket client, etc.
    html = """
    <!doctype html>
    <html>
      <head>
        <title>Microdot Server</title>
        <meta charset="UTF-8">
      </head>
      <body>
        <h1>Welcome to the BioIoT Server</h1>
        <p>Use /test for AWS IoT testing.</p>
      </body>
    </html>
    """
    return html

@app.route('/ws')
@with_websocket
async def ws_handler(request, ws):
    global last_heartbeat
    client_id = id(ws)
    print("WebSocket client connected:", client_id)
    while True:
        try:
            await ws.send("PING")
            data = await ws.receive()
            if data is None:
                print("Connection lost from", client_id)
                break
            if data.strip() == "PONG":
                last_heartbeat = time.ticks_ms()
                # Update heartbeat timestamp or similar logic here if needed
                print("Received PONG from", client_id)
            else:
                print("Received from", client_id, ":", data)
                await ws.send("Echo: " + data)
            await asyncio.sleep(0)
        except Exception as e:
            print("Exception in ws_handler for client", client_id, ":", e)
            break
    try:
        await ws.close()
    except Exception as close_err:
        print("Error closing websocket:", close_err)
    print("WebSocket client disconnected:", client_id)
    return ''

@app.route('/clients')
async def clients_list(request):
    result = {str(cid): {"last_heartbeat": info["last_heartbeat"]} for cid, info in clients.items()}
    return result


@app.route('/test', methods=['GET'])
async def test_page(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BioIoT Test Page</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial; padding: 20px; max-width: 600px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; box-sizing: border-box; }
            button { background: #4CAF50; color: white; border: none; padding: 10px 15px; cursor: pointer; }
            #response { margin-top: 20px; padding: 10px; background: #f0f0f0; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>BioIoT Test Console</h1>
        
        <div class="form-group">
            <label for="device_id">Device ID:</label>
            <input type="text" id="device_id" value="test_device">
        </div>
        
        <div class="form-group">
            <label for="sensor_data">Sensor Data (JSON):</label>
            <textarea id="sensor_data" rows="8">
{
  "nh3": 12.34,
  "h2s": 56.78,
  "air_pressure": 1013.25,
  "temperature_ambient": 25.5,
  "temperature_liquid": 23.1,
  "level": 78.9
}
            </textarea>
        </div>
        
        <button onclick="sendData()">Send Data to AWS</button>
        
        <div id="response"></div>
        
        <script>
            async function sendData() {
                const deviceId = document.getElementById('device_id').value;
                let sensorData;
                
                try {
                    sensorData = JSON.parse(document.getElementById('sensor_data').value);
                } catch(e) {
                    document.getElementById('response').textContent = 'Error: Invalid JSON data';
                    return;
                }
                
                const payload = {
                    device_id: deviceId,
                    timestamp: Math.floor(Date.now() / 1000),
                    sensors: sensorData
                };
                
                document.getElementById('response').textContent = 'Sending data...';
                
                try {
                    const response = await fetch('/sensors/data', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    
                    const result = await response.json();
                    document.getElementById('response').textContent = 'Response: ' + JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById('response').textContent = 'Error: ' + e.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return Response(body=html, headers={"Content-Type": "text/html"})

@app.route('/sensors/data', methods=['POST'])
async def sensors_data(request):
    try:
        # Get JSON data from POST
        data = request.json
        if not data:
            raise Exception("No JSON data provided")
        
        # Convert from form format to what AWS expects (rename "sensors" to "data")
        payload = {
            "device_id": data.get("device_id", "unknown"),
            "timestamp": data.get("timestamp", 0),
            "data": data.get("sensors", {})
        }
        
        print("Received sensor data:", payload)
        aws_result = send_to_aws(payload)
        response = {"status": "success" if aws_result else "failure", "payload": payload}
    except Exception as e:
        response = {"status": "error", "error": str(e)}
    return response

@app.route('/aws/synthetic', methods=['GET'])
async def aws_synthetic(request):
    # Generate synthetic sensor data with random values
    sensor_data = {
        "nh3": round(random.uniform(0, 100), 2),
        "h2s": round(random.uniform(0, 100), 2),
        "air_pressure": round(random.uniform(900, 1100), 2),
        "temperature_ambient": round(random.uniform(15, 35), 2),
        "temperature_liquid": round(random.uniform(15, 35), 2),
        "level": round(random.uniform(0, 100), 2)
    }
    payload = {
        "device_id": "test",
        "timestamp": int(time.time()),
        "sensors": sensor_data
    }
    # Adjust to AWS format by renaming "sensors" to "data"
    payload_for_aws = {
        "device_id": payload["device_id"],
        "timestamp": payload["timestamp"],
        "data": payload["sensors"]
    }
    print("Sending synthetic data to AWS:", payload_for_aws)
    aws_result = send_to_aws(payload_for_aws)
    return {"synthetic_data": payload, "aws_result": "success" if aws_result else "failure"}

  
async def start_websocket_server():
    await app.start_server(host="0.0.0.0", port=80)
