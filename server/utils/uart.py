#server/utils/uart.py

from machine import UART, Pin
from config.server_settings import TX_PIN, RX_PIN, UART_CHANNEL, UART_BAUDRATE

uart = UART(UART_CHANNEL, baudrate=UART_BAUDRATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
