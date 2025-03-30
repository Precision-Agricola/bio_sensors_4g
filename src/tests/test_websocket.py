import uasyncio as asyncio
from local_network.wifi import connect_wifi
from local_network.ws_client import connect_ws

SERVER_URI = "ws://192.168.4.1/ws"

async def ws_client():
    while True:
        ws = None
        try:
            print("Checking WiFi connectivity...")
            if not connect_wifi():
                print("WiFi not connected. Waiting 5 seconds before retrying...")
                await asyncio.sleep(5)
                continue

            print("WiFi connected. Attempting to connect to", SERVER_URI)
            ws = connect_ws(SERVER_URI)
            print("Connected to WebSocket!")
            while True:
                msg = ws.recv()  # blocking call – assumes small messages
                if msg is None:
                    raise Exception("Connection lost (received None)")
                print("Received:", msg)
                if msg.strip() == "PING":
                    ws.send("PONG")
                    print("Sent: PONG")
                # Adjust sleep as needed based on your communication frequency
                await asyncio.sleep(15)
        except Exception as e:
            print("Error:", e, "- reconnecting in 3 seconds...")
            try:
                ws.close()
            except Exception as close_err:
                print("Error closing WebSocket:", close_err)
            await asyncio.sleep(3)

if __name__ == '__main__':
    asyncio.run(ws_client())
