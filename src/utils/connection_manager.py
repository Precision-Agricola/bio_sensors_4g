import uasyncio as asyncio
import time
from local_network.ws_client import connect_ws

class ConnectionManager:
    def __init__(self, uri="ws://192.168.4.1/ws"):
        self.uri = uri
        self.ws = None
        self.connected = False
        self.retry_count = 0
        self.max_retries = 5

    async def connect(self):
        while True:
            try:
                if self.retry_count >= self.max_retries:
                    print("Max retries reached. Cooling down...")
                    await asyncio.sleep(30)
                    self.retry_count = 0

                print("ConnectionManager: Attempting connection to", self.uri)
                self.ws = connect_ws(self.uri, timeout=10)
                self.connected = True
                self.retry_count = 0
                print("ConnectionManager: Connected")
                return
            except Exception as e:
                print(f"ConnectionManager: Connection error ({self.retry_count}/{self.max_retries}):", e)
                self.connected = False
                self.retry_count += 1
                await asyncio.sleep(2 + self.retry_count*2)

    async def run(self):
        while True:
            if not self.connected:
                await self.connect()
            try:
                # Use non-blocking receive with timeout
                msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                if msg is None:
                    raise Exception("Connection closed by server")
                    
                print("Received:", msg)
                if msg.strip() == "HEARTBEAT":
                    await self.send("PONG")
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                print("No data received, sending keepalive")
                await self.send("PING")
            except Exception as e:
                print("Connection error:", e)
                await self.handle_disconnect()

    async def handle_disconnect(self):
        self.connected = False
        try:
            if self.ws:
                self.ws.close()
        except Exception as e:
            print("Cleanup error:", e)
        finally:
            self.ws = None
            await asyncio.sleep(1)

    async def send(self, message):
        if not self.connected:
            await self.connect()
            
        if self.connected:
            try:
                self.ws.send(message)
                print("Sent:", message)
            except Exception as e:
                print("Send error:", e)
                await self.handle_disconnect()
