import uasyncio as asyncio
import time
from local_network.ws_client import connect_ws

class ConnectionManager:
    def __init__(self, uri="ws://192.168.4.1/ws"):
        self.uri = uri
        self.ws = None
        self.connected = False

    async def connect(self):
        """Try to connect and update connection status."""
        while True:
            try:
                print("ConnectionManager: Attempting connection to", self.uri)
                self.ws = connect_ws(self.uri)
                self.connected = True
                print("ConnectionManager: Connected")
                return
            except Exception as e:
                print("ConnectionManager: Connection error:", e)
                self.connected = False
                await asyncio.sleep(3)

    async def run(self):
        """Keep the connection alive and process incoming messages."""
        while True:
            if not self.connected:
                await self.connect()
            try:
                # Blocking call from our simple client; messages are assumed to be short.
                msg = self.ws.recv()
                if msg is None:
                    raise Exception("Connection closed by server")
                print("ConnectionManager: Received message:", msg)
                # Handle heartbeat (ping–pong) logic.
                if msg.strip() == "HEARTBEAT":
                    self.ws.send("PONG")
                    print("ConnectionManager: Sent PONG")
                # You can add processing for other messages here.
                await asyncio.sleep(0)
            except Exception as e:
                print("ConnectionManager: Error in connection:", e)
                self.connected = False
                try:
                    self.ws.close()
                except Exception as close_err:
                    print("ConnectionManager: Error closing connection:", close_err)
                await asyncio.sleep(3)

    async def send(self, message):
        """Send a message if connected; otherwise, drop or queue it."""
        if self.connected and self.ws:
            try:
                self.ws.send(message)
                print("ConnectionManager: Sent message:", message)
            except Exception as e:
                print("ConnectionManager: Error sending message:", e)
                self.connected = False
                try:
                    self.ws.close()
                except Exception:
                    pass

