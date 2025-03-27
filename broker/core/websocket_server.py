import uasyncio as asyncio
import time
from microdot import Microdot, Response, send_file
from websocket import with_websocket

Response.default_content_type = 'text/html'

app = Microdot()
clients = {}

@app.route('/')
async def index(request):
    # Basic HTML page that opens a WebSocket connection.
    html = """
    <!doctype html>
    <html>
      <head>
        <title>WebSocket with Heartbeat</title>
        <meta charset="UTF-8">
      </head>
      <body>
        <h1>WebSocket with Heartbeat Demo</h1>
        <p>Open the console to see messages.</p>
        <script>
          const connect = () => {
            const socket = new WebSocket('ws://' + location.host + '/ws');
            socket.onmessage = ev => {
              console.log('Server:', ev.data);
              if(ev.data === 'PING') {
                socket.send('PONG');
              }
            };
            socket.onclose = () => {
              console.log('Socket closed, reconnecting in 3 seconds...');
              setTimeout(connect, 3000);
            };
          };
          connect();
        </script>
      </body>
    </html>
    """
    return html

@app.route('/ws')
@with_websocket
async def ws_handler(request, ws):
    client_id = id(ws)
    clients[client_id] = {'ws': ws, 'last_heartbeat': time.time()}
    heartbeat_interval = 5
    heartbeat_timeout = 3
    max_missed = 3
    missed = 0

    while True:
        try:
            await ws.send("PING")
            try:
                data = await asyncio.wait_for(ws.receive(), timeout=heartbeat_timeout)
            except asyncio.TimeoutError:
                missed += 1
                print("Missed heartbeat from client", client_id, "count:", missed)
                if missed >= max_missed:
                    print("Disconnecting client", client_id)
                    break
                continue
            missed = 0
            if data.strip() == "PONG":
                clients[client_id]['last_heartbeat'] = time.time()
            else:
                print("Received from client", client_id, ":", data)
                await ws.send("Echo: " + data)
        except Exception as e:
            print("Exception in ws_handler for client", client_id, ":", e)
            break

    clients.pop(client_id, None)
    try:
        await ws.close()
    except Exception as close_err:
        print("Error closing websocket:", close_err)
    return ''

@app.route('/clients')
async def clients_list(request):
    result = {str(cid): {"last_heartbeat": info["last_heartbeat"]} for cid, info in clients.items()}
    return result

@app.route('/test')
async def test(request):
    return "Connection OK"

async def start_websocket_server():
    await app.start_server(host="0.0.0.0", port=80)

