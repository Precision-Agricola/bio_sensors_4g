# broker/core/http_server.py
from microdot import Microdot, Response
import json
import time

# Create the application
app = Microdot()
received_data = []
pending_commands = []

@app.route('/')
def index(request):
    """Root endpoint - returns system status"""
    from core.stats import get_statistics
    
    stats = get_statistics()
    
    return Response(
        json.dumps({
            "status": "running",
            "uptime": time.time(),
            "statistics": stats
        }),
        headers={"Content-Type": "application/json"}
    )

@app.route('/sensors/data', methods=['POST'])
def receive_data(request):
    """Endpoint to receive sensor data from devices"""
    from core.data_handler import process_sensor_data
    
    try:
        if not request.json:
            return Response(
                json.dumps({"error": "Invalid JSON data"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Process the data
        result = process_sensor_data(request.json)
        
        return Response(
            json.dumps({"status": "success", "message": "Data received"}),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        import sys
        sys.print_exception(e)
        return Response(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

@app.route('/command/<device_id>', methods=['POST'])
def send_command(request, device_id):
    """Endpoint to queue commands for devices"""
    from core.data_handler import queue_command
    
    try:
        if not request.json or 'command' not in request.json:
            return Response(
                json.dumps({"error": "Invalid command request"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        command = request.json['command']
        params = request.json.get('params', {})
        
        # Queue the command
        cmd_id = queue_command(device_id, command, params)
        
        return Response(
            json.dumps({
                "status": "success", 
                "message": f"Command queued for {device_id}",
                "command_id": cmd_id
            }),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        import sys
        sys.print_exception(e)
        return Response(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

@app.route('/commands/<device_id>', methods=['GET'])
def get_commands(request, device_id):
    """Endpoint for devices to fetch pending commands"""
    from core.data_handler import get_pending_commands
    
    # Get commands for the device
    commands = get_pending_commands(device_id)
    
    return Response(
        json.dumps({
            "device_id": device_id,
            "commands": commands
        }),
        headers={"Content-Type": "application/json"}
    )

def start_server(host='0.0.0.0', port=80):
    """Start the HTTP server"""
    print(f"Starting HTTP server on {host}:{port}")
    app.run(host=host, port=port)

@app.route('/test')
def test_page(request):
    """HTML page for testing from a mobile phone"""
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
            <textarea id="sensor_data" rows="8">{"temperature": 25.5, "humidity": 60, "pressure": 1013.25}</textarea>
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
                    data: sensorData
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
    return Response(
        body=html,
        headers={"Content-Type": "text/html"}
    )