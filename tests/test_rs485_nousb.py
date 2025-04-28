"""The following code works by connecting a 10kR from IO3 (RX) to 3.3V"""

from machine import UART, Pin
import time
import struct


DIP_SW1 = Pin(26, Pin.IN, Pin.PULL_DOWN)
END_R = Pin(12, Pin.OUT)
END_R.value(0)
log_path = 'log485.txt'

def log(msg):
    with open(log_path, 'a') as f:
        f.write(f"{time.time():.0f}: {msg}\n")
        f.flush()

if  DIP_SW1.value():
    log("testing sensor mode")

    # UART2 con pull-up en RX
    
    Pin(3, Pin.IN, Pin.PULL_UP)
    Pin(2, Pin.IN, Pin.PULL_UP)
    time.sleep(1)
    uart = UART(2, baudrate=9600, tx=1, rx=3)

    de_re = Pin(22, Pin.OUT)

    comando_1 = b'\x01\x03\x04\x0a\x00\x02\xE5\x39'
    comando_2 = b'\x01\x03\x04\x08\x00\x02\x44\xF9'
    comando_3 = b'\x01\x03\x04\x0c\x00\x02\x05\x38'

    def ieee754_to_float(b):
        return struct.unpack('>f', b)[0]

    def send_and_receive(cmd):
        log(f"Enviando: {cmd.hex()}")
        de_re.on()

        uart.write(cmd)

        time.sleep_ms(10)
        de_re.off()
        time.sleep_ms(5)

        for i in range(5):
            time.sleep_ms(200)
            resp = uart.read(20)
            if resp:
                log(f"Respuesta[{i+1}]: {resp.hex()}")
                if (
                    len(resp) == 9 and
                    resp[0] == 0x01 and
                    resp[1] == 0x03 and
                    resp[2] == 0x04 and
                    any(b != 0 for b in resp[3:7])
                ):
                    try:
                        val = ieee754_to_float(resp[3:7])
                        log(f"Valor float: {val}")
                        return
                    except Exception as e:
                        log(f"Error conversión: {e}")
            else:
                log(f"Sin respuesta en intento {i+1}")

        log("Fallo en obtener respuesta válida")

    try:
        send_and_receive(comando_1)
        time.sleep(1)
        send_and_receive(comando_2)
        time.sleep(1)
        send_and_receive(comando_3)
    finally:
        END_R.value(1)
        uart.deinit()
        log("UART deshabilitado")
else:
    log("Modo BOOT o TEST activo, REPL disponible.")



