# main.py
import time
import network
import socket
import gc  # Garbage Collection module
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

# --- Configuration ---
MODEM_FILE_NAME = "client.zip"
AP_SSID = "PicoFileServer"
AP_PASSWORD = "password123"

# --- PicoLTE Initialization ---
print("--- Pico W Modem File Server (Streaming Version 2.0) ---")
print("Initializing modem connection...")
try:
    lte = PicoLTE()
    print("Modem initialized successfully.")
except Exception as e:
    print(f"[FATAL ERROR] Failed to initialize PicoLTE: {e}")
    while True: time.sleep(5)

# --- Wi-Fi Access Point Setup Function ---
def setup_access_point():
    print("\n--- Step 1: Setting up Wi-Fi Access Point ---")
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=AP_SSID, password=AP_PASSWORD)
    ap.active(True)
    while not ap.active():
        time.sleep(1)
    ip_address = ap.ifconfig()[0]
    print(f"Access Point enabled successfully!")
    print(f" -> Wi-Fi Name (SSID): {AP_SSID}")
    print(f" -> Wi-Fi Password:    {AP_PASSWORD}")
    print(f"\nZIP file will be served on: http://{ip_address}")
    return ip_address

# --- Modem File Verification Function ---
def check_modem_file():
    print("\n--- Step 2: Verifying file on modem ---")
    result = lte.file.get_file_list(MODEM_FILE_NAME)
    if result.get('status') == Status.SUCCESS and result.get('response'):
        for line in result['response']:
            if line.startswith('+QFLST:'):
                parts = line.split(',')
                filename_part = parts[0].split(':')[1].strip().strip('"')
                filesize = parts[1].strip()
                if filename_part == MODEM_FILE_NAME:
                    print(f"File found in modem with the next details:")
                    print(f" -> Filename: {filename_part}")
                    print(f" -> Size: {filesize} bytes")
                    return int(filesize)
    print(f"[ERROR] File '{MODEM_FILE_NAME}' not found on the modem!")
    return None

# --- FINAL: Function to stream the file using correct UART methods ---
def stream_file_to_client(client_socket, file_size):
    """
    Reads the file from the modem in chunks using the direct UART object
    `lte.atcom.modem_com` and writes each chunk to the client socket.
    """
    print("\n--- Step 3: Streaming file to client ---")
    # Get the correct, low-level UART object from the ATCom instance
    uart = lte.atcom.modem_com

    # 3a: Send HTTP headers to the client
    print("Sending HTTP headers...")
    client_socket.send(b'HTTP/1.1 200 OK\r\n')
    client_socket.send(b'Content-Type: application/zip\r\n')
    client_socket.send(f'Content-Length: {file_size}\r\n'.encode())
    client_socket.send(b'Content-Disposition: attachment; filename="client.zip"\r\n')
    client_socket.send(b'Connection: close\r\n\r\n')

    # 3b: Send the download command and manually wait for "CONNECT"
    command = f'AT+QFDWL="{MODEM_FILE_NAME}"\r\n'
    if uart.any(): uart.read()  # Clear UART buffer
    
    print(f"Sending command to modem: {command.strip()}")
    uart.write(command.encode('utf-8'))
    
    # Manually read lines until "CONNECT" is found
    connect_found = False
    start_time = time.ticks_ms()
    buffer = b''
    while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
        if uart.any():
            buffer += uart.read(1)
            if b'\n' in buffer:
                line = buffer.strip().decode('utf-8', 'ignore')
                print(f"Modem > {line}")
                if "CONNECT" in line:
                    connect_found = True
                    break
                if "ERROR" in line:
                    print("[ERROR] Modem returned an error.")
                    return False
                buffer = b''

    if not connect_found:
        print("[ERROR] Timeout: Did not receive 'CONNECT' from modem.")
        return False
        
    print("CONNECT received. Starting stream...")

    # 3c: The Streaming Loop
    bytes_sent = 0
    chunk_size = 2048
    gc.collect()

    while bytes_sent < file_size:
        try:
            bytes_to_read = min(chunk_size, file_size - bytes_sent)
            chunk_data = uart.read(bytes_to_read)
            if not chunk_data:
                print("\n[ERROR] UART read failed mid-stream.")
                return False
            client_socket.write(chunk_data)
            bytes_sent += len(chunk_data)
        except Exception as e:
            print(f"\n[ERROR] An error occurred during streaming: {e}")
            return False

    print(f"\nFinished streaming. Total bytes sent: {bytes_sent}")

    # 3d: Manually clean up final modem responses (+QFDWL and OK)
    print("Cleaning up final modem response...")
    cleanup_start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), cleanup_start_time) < 3000:
        if uart.any():
            response_bytes = uart.read()
            if response_bytes and b"OK" in response_bytes:
                print(f"Modem > {response_bytes.strip().decode('utf-8', 'ignore')}")
                break
    print("Modem state is clean.")
    return bytes_sent == file_size

# --- Main Program Execution ---
ip = setup_access_point()
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("\n--- Web server is now running ---")
print("Waiting for a client to connect...")

while True:
    gc.collect()
    try:
        cl, addr = s.accept()
        cl.settimeout(10)
        print(f"\n--- Client connected from: {addr} ---")
        request = cl.recv(1024)
        
        file_size = check_modem_file()
        if file_size:
            stream_file_to_client(cl, file_size)
        else:
            cl.send(b'HTTP/1.1 404 Not Found\r\n\r\nFile not found on modem.')

        cl.close()
        print("\n--- Waiting for next client ---")
    except OSError as e:
        if 'cl' in locals(): cl.close()
        print(f"[ERROR] A connection error occurred: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        break

if 's' in locals(): s.close()
print("Script finished.")