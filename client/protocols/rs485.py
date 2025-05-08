# main.py - runs after boot.py if in Sensing Mode
from machine import Pin, UART
import time
import network
import json
import struct
from utils.logger import log_message


# Initialize pins
boot_pin = Pin(25, Pin.IN, Pin.PULL_DOWN)
de_re = Pin(22, Pin.OUT)
working_relay = Pin(27, Pin.OUT)
fail_relay = Pin(12, Pin.OUT)

# Only run this code in Sensing Mode
if not boot_pin.value():
    # In programming mode, exit
    import sys
    sys.exit()

# RS485 functions
def send_rs485(data, uart, de_re):
    de_re.on()  # Transmission mode
    uart.write(data)
    time.sleep_ms(10)  # Wait for transmission
    de_re.off()  # Back to reception mode
    time.sleep_ms(100)  # Wait for response

def ieee754_to_float(bytes_data):
    # Convert 4 bytes to an IEEE-754 float
    return struct.unpack('>f', bytes_data)[0]

def decode_modbus_response(response):
    if not response or len(response) < 7:
        return None
    
    # Extract the relevant bytes (positions 3-6 contain the float data)
    relevant_bytes = response[3:7]
    
    # Convert to IEEE-754 float
    try:
        float_value = ieee754_to_float(relevant_bytes)
        return float_value
    except Exception as e:
        log_message(f"Error decoding float: {e}")
        return None

def blink_working_relay(count=1, duration=1):
    for _ in range(count):
        working_relay.value(1)
        time.sleep(duration)
        working_relay.value(0)
        if _ < count - 1:
            time.sleep(duration)

def blink_fail_relay(count=1, duration=3):
    for _ in range(count):
        fail_relay.value(1)
        time.sleep(duration)
        fail_relay.value(0)

# Setup WiFi in AP mode for monitoring
def setup_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="PrecisionAg-RS485", password="bioiot2025")
    while not ap.active():
        pass
    log_message("WiFi AP active:", ap.ifconfig())
    return ap

# Simple HTTP server for logs
def start_http_server():
    import socket
    
    # Create the HTML file in the filesystem
    try:
        with open('index.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Precisión Agrícola - RS485 Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; background-color: #f0f0f0; }
        .header { background-color: #4CAF50; color: white; padding: 10px; text-align: center; }
        .container { background-color: white; padding: 15px; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .success { color: green; }
        .error { color: red; }
        .refresh-btn { background-color: #4CAF50; color: white; padding: 10px 15px; 
                      border: none; cursor: pointer; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Precisión Agrícola - BIO-IOT</h1>
        <h2>RS485 Sensor Monitor</h2>
    </div>
    <div class="container">
        <button class="refresh-btn" onclick="fetchData()">Refresh Data</button>
        <div id="data-container">Loading...</div>
    </div>
    <script>
        function fetchData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    let html = '<h3>Sensor Readings</h3><table><tr><th>Time</th><th>Command</th>' +
                              '<th>Value</th><th>Status</th></tr>';
                    
                    data.forEach(item => {
                        const date = new Date(item.timestamp * 1000);
                        const time = date.toLocaleTimeString();
                        const status = item.status === 'success' ? 
                            '<span class="success">Success</span>' : 
                            '<span class="error">Failed</span>';
                        
                        html += '<tr><td>' + time + '</td><td>' + 
                               (item.command || '-') + '</td><td>' + 
                               (item.decoded_value !== undefined ? item.decoded_value : '-') + 
                               '</td><td>' + status + '</td></tr>';
                    });
                    
                    html += '</table>';
                    document.getElementById('data-container').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('data-container').innerHTML = 
                        '<p class="error">Error: ' + error.message + '</p>';
                });
        }
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>''')
    except Exception as e:
        log_message(f"Error creating HTML file: {e}")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    return s

# Log buffer to store sensor readings
log_buffer = []

# Main function
def main():
    global log_buffer
    
    # Setup UART for RS485 - Fixed line
    try:
        # The corrected line: UART2 with proper pin assignments
        uart = UART(2, baudrate=9600, tx=1, rx=3)  # Using recommended GPIO pins for UART2
        blink_working_relay(2)  # Indicate successful UART setup
    except Exception as e:
        log_message(f"UART setup failed: {e}")
        blink_fail_relay()
        return
    
    # Setup WiFi
    ap = setup_wifi()
    
    # Start HTTP server
    http_server = start_http_server()
    log_message("HTTP server started")
    
    # RS485 test commands (Modbus read holding registers)
    command_1 = b'\x01\x03\x04\x0a\x00\x02\xE5\x39'  # Original command
    command_2 = b'\x01\x03\x04\x0c\x00\x02\x05\x38'  # Second command
    # Main loop
    while True:
        try:
            # Send first RS485 command
            send_rs485(command_1, uart, de_re)
            
            # Wait for response
            time.sleep(0.5)
            response1 = uart.read()
            
            # Process first response
            timestamp = time.time()
            cmd1_value = None
            
            if response1:
                # Successful reading
                blink_working_relay(1, 0.2)
                hex_response = ' '.join([f'{b:02X}' for b in response1])
                
                # Decode the float value
                cmd1_value = decode_modbus_response(response1)
                
                # Add to log buffer (limit size)
                log_entry = {
                    "timestamp": timestamp,
                    "command": "cmd1",
                    "raw_data": hex_response,
                    "decoded_value": cmd1_value,
                    "status": "success"
                }
                
                log_buffer.append(log_entry)
                if len(log_buffer) > 20:  # Keep only last 20 readings
                    log_buffer.pop(0)
            else:
                # Failed reading
                blink_fail_relay(1, 0.5)
                log_entry = {
                    "timestamp": timestamp,
                    "command": "cmd1",
                    "status": "no_response"
                }
                log_buffer.append(log_entry)
            
            # Wait between commands
            time.sleep(2)
            
            # Send second RS485 command
            send_rs485(command_2, uart, de_re)
            
            # Wait for response
            time.sleep(0.5)
            response2 = uart.read()
            
            # Process second response
            timestamp = time.time()
            cmd2_value = None
            
            if response2:
                # Successful reading
                blink_working_relay(1, 0.2)
                hex_response = ' '.join([f'{b:02X}' for b in response2])
                
                # Decode the float value
                cmd2_value = decode_modbus_response(response2)
                
                # Add to log buffer (limit size)
                log_entry = {
                    "timestamp": timestamp,
                    "command": "cmd2",
                    "raw_data": hex_response,
                    "decoded_value": cmd2_value,
                    "status": "success"
                }
                
                log_buffer.append(log_entry)
                if len(log_buffer) > 20:  # Keep only last 20 readings
                    log_buffer.pop(0)
            else:
                # Failed reading
                blink_fail_relay(1, 0.5)
                log_entry = {
                    "timestamp": timestamp,
                    "command": "cmd2",
                    "status": "no_response"
                }
                log_buffer.append(log_entry)
            
            # Check for HTTP connections
            try:
                conn, addr = http_server.accept()
                request = conn.recv(1024)
                request_str = request.decode()
                
                # Check the request path
                if 'GET /data' in request_str:
                    # Return JSON data
                    response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                    response += json.dumps(log_buffer)
                elif 'GET /' in request_str:
                    # Return the HTML page
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                    try:
                        with open('index.html', 'r') as f:
                            response += f.read()
                    except:
                        response += "<html><body><h1>Error loading page</h1></body></html>"
                else:
                    # Not found
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
                
                conn.send(response)
                conn.close()
            except OSError:
                # No connection available, continue
                pass
                
            # Wait before next reading
            time.sleep(5)
            
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            blink_fail_relay()
            time.sleep(10)

# Run the main function
if __name__ == "__main__":
    main()