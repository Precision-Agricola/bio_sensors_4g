"""RS485 Wrapper"""
from machine import Pin, UART
import time
import struct
from config.config import RS485_TX_PIN, RS485_RX_PIN, RS485_DE_RE_PIN

class RS485Device:
    """
    Clase que representa un dispositivo RS485.
    
    Args:
        uart_id (int): ID del UART a utilizar (1 o 2)
        baudrate (int): Velocidad en baudios
        tx_pin (int): Número de pin para TX. Por defecto usa RS485_TX_PIN de config.
        rx_pin (int): Número de pin para RX. Por defecto usa RS485_RX_PIN de config.
        de_re_pin (int): Número de pin para DE/RE. Por defecto usa RS485_DE_RE_PIN de config.
    """
    def __init__(self, uart_id=2, baudrate=9600, tx_pin=None, rx_pin=None, de_re_pin=None):
        tx = tx_pin if tx_pin is not None else RS485_TX_PIN
        rx = rx_pin if rx_pin is not None else RS485_RX_PIN
        de_re = de_re_pin if de_re_pin is not None else RS485_DE_RE_PIN
        
        self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx)
        self.de_re = Pin(de_re, Pin.OUT)
        self.de_re.off()
    
    def send_command(self, command, response_timeout=0.5):
        """
        Envía un comando a través de RS485 y recibe la respuesta.
        
        Args:
            command (bytes): Comando a enviar
            response_timeout (float): Tiempo de espera para la respuesta en segundos
            
        Returns:
            bytes: Respuesta recibida o None si no hay respuesta
        """
        self.de_re.on()
        self.uart.write(command)
        time.sleep_ms(10)
        self.de_re.off() 
        
        time.sleep(response_timeout)
        return self.uart.read()
    
    def ieee754_to_float(self, bytes_data):
        """
        Convierte 4 bytes a un número flotante IEEE-754.
        
        Args:
            bytes_data (bytes): 4 bytes en formato IEEE-754
            
        Returns:
            float: Valor convertido
        """
        return struct.unpack('>f', bytes_data)[0]
    
    def decode_modbus_response(self, response):
        """
        Decodifica una respuesta Modbus que contiene un valor flotante.
        
        Args:
            response (bytes): Respuesta completa del protocolo Modbus
            
        Returns:
            float: Valor decodificado o None si hay error
        """
        if not response or len(response) < 7:
            return None
        
        relevant_bytes = response[3:7]
        try:
            float_value = self.ieee754_to_float(relevant_bytes)
            return float_value
        except Exception as e:
            print(f"Error decodificando float: {e}")
            return None

def init_rs485(uart_id=2, baudrate=9600, tx_pin=None, rx_pin=None, de_re_pin=None):
    """
    Función de conveniencia para inicializar el dispositivo RS485 con los parámetros especificados.
    Si no se especifican, se usan los valores de config.
    
    Returns:
        RS485Device: Objeto RS485Device configurado.
    """
    return RS485Device(uart_id=uart_id, baudrate=baudrate, tx_pin=tx_pin, rx_pin=rx_pin, de_re_pin=de_re_pin)
