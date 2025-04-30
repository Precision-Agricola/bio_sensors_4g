import uasyncio as asyncio
import time
import random
import machine
from microdot import Microdot, Response
from websocket import with_websocket
from core.aws_forwarding import send_to_aws

# --- Global State ---
# Diccionario para almacenar información de clientes conectados
# Clave: client_id, Valor: diccionario con info del cliente
clients = {}

PING_INTERVAL_S = 25
CLIENT_TIMEOUT_S = PING_INTERVAL_S * 3 

# Configure watchdog with maximum (8 seconds)
wdt = machine.WDT(timeout=8000)
last_heartbeat = time.ticks_ms()  # Global timestamp

async def send_to_aws_background_wrapper(payload):
    try:
        success = send_to_aws(payload)
        print(f"Background AWS send result for {payload.get('device_id')}: {'Success' if success else 'Failure'}")
        print(f"Payload: {payload}")
    except Exception as e:
        print(f"Exception in background send_to_aws task: {e}")
        import sys
        sys.print_exception(e)

# --- Watchdog Feeder Task ---
async def watchdog_feeder():
    """
    Alimenta el WDT periódicamente SI HAY clientes conectados.
    Si no hay clientes conectados durante un tiempo, deja de alimentar
    permitiendo que el WDT reinicie el sistema si se queda 'colgado' sin clientes.
    """
    print("Watchdog feeder task started.")
    NO_CLIENT_RESET_DELAY_S = 5 * 60 # 5 minutos: Tiempo sin clientes antes de dejar de alimentar WDT
    last_client_seen_time = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        if clients: # Si el diccionario de clientes NO está vacío
            last_client_seen_time = now # Actualizar timestamp de último cliente visto
            # print("WDT Fed (Clients Connected)") # Debug log - puede ser ruidoso
            wdt.feed()
        else:
            # No hay clientes conectados
            if time.ticks_diff(now, last_client_seen_time) > NO_CLIENT_RESET_DELAY_S * 1000:
                print(f"WDT: No clients connected for {NO_CLIENT_RESET_DELAY_S}s. Stopping feed to allow potential reset.")
                # Dejamos de alimentar. Si el sistema está bien pero sin clientes,
                # seguirá funcionando. Si está colgado, el WDT lo reiniciará.
                # Rompemos el bucle para dejar de alimentar definitivamente hasta el próximo reinicio.
                break
            else:
                # Aún estamos en el periodo de gracia sin clientes, seguimos alimentando.
                wdt.feed()
        await asyncio.sleep(1)

app = Microdot()
Response.default_content_type = 'text/html'

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
# --- WebSocket Handler ---
@app.route('/ws')
@with_websocket
async def ws_handler(request, ws):
    client_id = str(id(ws)) # Usar string como ID
    client_ip = request.client_addr[0] if request.client_addr else "Unknown IP"
    connect_time = time.ticks_ms()
    client_info = {
        "ws": ws,
        "ip": client_ip,
        "connect_time_ms": connect_time,
        "last_pong_time_ms": connect_time # Inicializar al tiempo de conexión
    }
    clients[client_id] = client_info
    print(f"WebSocket client connected: ID={client_id}, IP={client_ip}")
    print(f"Total clients: {len(clients)}")

    try:
        while True:

            await asyncio.sleep(PING_INTERVAL_S)
            try:
                await ws.send("PING")
                ping_sent_time = time.ticks_ms()
            except Exception as send_err:
                print(f"Error sending PING to {client_id}: {send_err}")
                break

            try:
                data = await ws.receive()
            except Exception as recv_err:
                 print(f"Error receiving data from {client_id}: {recv_err}")
                 break

            if data is None:
                print(f"Connection closed by client {client_id}")
                break

            now = time.ticks_ms()
            if isinstance(data, str) and data.strip().upper() == "PONG":
                clients[client_id]["last_pong_time_ms"] = now
                print(f"Received PONG from {client_id}") # TODO: remove after tests
            else:
                print(f"Received data from {client_id}: {data}")
                # Procesar los datos como sea necesario aquí
                # await ws.send("Echo: " + data) # Eliminar/modificar el echo si no es necesario

            last_pong = clients[client_id]["last_pong_time_ms"]
            if time.ticks_diff(now, last_pong) > CLIENT_TIMEOUT_S * 1000:
                print(f"Client {client_id} timed out (No PONG received for {CLIENT_TIMEOUT_S}s). Disconnecting.")
                break

    except Exception as e:
        print(f"Unhandled exception in ws_handler for client {client_id}: {e}")
    finally:
        print(f"Disconnecting client {client_id}...")
        try:
            await ws.close()
        except Exception as close_err:
            print(f"Error closing websocket for {client_id}: {close_err}")
        if client_id in clients:
            del clients[client_id]
            print(f"Client {client_id} removed from registry.")
        print(f"Total clients remaining: {len(clients)}")


@app.route('/clients')
async def clients_list(request):
    now = time.ticks_ms()
    client_data = {}
    for cid, info in clients.items():
        client_data[cid] = {
            "ip": info.get("ip", "N/A"),
            "connected_since_ms": time.ticks_diff(now, info.get("connect_time_ms", now)),
            "last_pong_since_ms": time.ticks_diff(now, info.get("last_pong_time_ms", now))
        }
    return Response(body=client_data, headers={"Content-Type": "application/json"})



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
    wdt.feed()
    try:
        data = request.json
        if not data: raise ValueError("No JSON data provided")
        payload_for_aws = {
             "device_id": data.get("device_id", "unknown"),
             "timestamp": data.get("timestamp", int(time.time())),
             "data": data.get("sensors", {}),
             "aerator_status": data.get("aerator_status", "UNKNOWN") 
         }
        wdt.feed()
        print("Received sensor data, queuing for AWS send:", payload_for_aws.get('device_id'))
        wdt.feed()
        asyncio.create_task(send_to_aws_background_wrapper(payload_for_aws)) 
        response = {"status": "queued", "message": "Data received and queued for sending to AWS."}

    except Exception as e:
        print(f"Error processing /sensors/data request: {e}")
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
    try:
        asyncio.create_task(send_to_aws_background_wrapper(payload_for_aws))
        response = {"status": "queued", "message": "Synthetic data queued for sending to AWS.", "data_generated": payload}
    except Exception as e:
        print(f"Error processing /aws/synthetic request: {e}")
        response = {"status": "error", "error": str(e)}
    return response  

async def start_websocket_server():
    print(f"Starting Microdot server on 0.0.0.0:80...")
    try:
        await app.start_server(host="0.0.0.0", port=80, debug=False)
    except Exception as e:
        print(f"FATAL ERROR starting server: {e}")
