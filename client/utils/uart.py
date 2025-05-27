# client/utils/uart.py

from machine import UART, Pin

uart = UART(1, tx=Pin(0), rx=Pin(2), baudrate=9600)
