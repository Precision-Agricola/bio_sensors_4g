# main.py - runs after boot.py if in Sensing Mode
from machine import Pin, UART
import time
import network
import json

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
    print("WiFi AP active:", ap.ifconfig())
    return ap

# Simple HTTP server for logs
def start_http_server():
    import socket
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
        print(f"UART setup failed: {e}")
        blink_fail_relay()
        return
    
    # Setup WiFi
    ap = setup_wifi()
    
    # Start HTTP server
    http_server = start_http_server()
    print("HTTP server started")
    
    # RS485 test command (Modbus read holding registers)
    command_1 = b'\x01\x03\x04\x0a\x00\x02\xE5\x39'
    
    # Main loop
    while True:
        try:
            # Send RS485 command
            send_rs485(command_1, uart, de_re)
            
            # Wait for response
            time.sleep(0.5)
            response = uart.read()
            
            # Process response
            timestamp = time.time()
            
            if response:
                # Successful reading
                blink_working_relay(1, 0.5)
                hex_response = ' '.join([f'{b:02X}' for b in response])
                
                # Add to log buffer (limit size)
                log_entry = {
                    "timestamp": timestamp,
                    "data": hex_response,
                    "status": "success"
                }
                
                log_buffer.append(log_entry)
                if len(log_buffer) > 20:  # Keep only last 20 readings
                    log_buffer.pop(0)
            else:
                # Failed reading
                blink_fail_relay(1, 1)
                log_entry = {
                    "timestamp": timestamp,
                    "status": "no_response"
                }
                log_buffer.append(log_entry)
            
            # Check for HTTP connections
            try:
                conn, addr = http_server.accept()
                request = conn.recv(1024)
                
                # Simple HTTP response with log data
                response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
                response += json.dumps(log_buffer)
                
                conn.send(response)
                conn.close()
            except OSError:
                # No connection available, continue
                pass
                
            # Wait before next reading
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            blink_fail_relay()
            time.sleep(10)

# Run the main function
if __name__ == "__main__":
    main()
