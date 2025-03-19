"""Liquid Pressure Sensor SW-P300 using RS485/Modbus"""
from sensors.base import Sensor, register_sensor
from machine import Pin, UART
import time
import struct

@register_sensor("SW-P300", "RS485")
class SWP300Sensor(Sensor):
    def __init__(self, name, model, protocol, vin, **kwargs):
        if 'signal' not in kwargs:
            kwargs['signal'] = 0
        
        # Usar exactamente los mismos comandos que funcionaron en el código de depuración
        self.cmd_pressure = b'\x01\x03\x04\x0a\x00\x02\xE5\x39'
        self.cmd_temperature = b'\x01\x03\x04\x0c\x00\x02\x05\x38'
        
        super().__init__(name, model, protocol, vin, **kwargs)
    
    def _init_hardware(self):
        super()._init_hardware()
        
        # Inicializar UART y pin DE/RE exactamente como en el código de depuración
        self.uart = UART(2, baudrate=9600, tx=1, rx=3)
        self.de_re = Pin(22, Pin.OUT)
        self.de_re.off() 
        
        self._initialized = True
        self._log_debug(f"Hardware inicializado para {self.name}")

    def read(self):
        if not getattr(self, '_initialized', False):
            self._init_hardware()
        result = self._read_implementation()
        self._log_debug(f"Metodo read() retornado: {result}")
        return result 
        
    def _read_implementation(self):
        try:
            self._log_debug(f"Iniciando lectura de {self.name}")
            
            # Leer presión
            self._log_debug("Enviando comando de presión")
            pressure_response = self._send_rs485(self.cmd_pressure)
            pressure_value = None
            
            if pressure_response:
                hex_response = ' '.join([f'{b:02X}' for b in pressure_response])
                self._log_debug(f"Respuesta presión (hex): {hex_response}")
                pressure_value = self._decode_modbus_response(pressure_response)
                self._log_debug(f"Presión decodificada: {pressure_value}")
            else:
                self._log_debug("No se recibió respuesta de presión")
            
            # Esperar entre comandos
            time.sleep(2)
            
            # Leer temperatura
            self._log_debug("Enviando comando de temperatura")
            temp_response = self._send_rs485(self.cmd_temperature)
            temp_value = None
            
            if temp_response:
                hex_response = ' '.join([f'{b:02X}' for b in temp_response])
                self._log_debug(f"Respuesta temperatura (hex): {hex_response}")
                temp_value = self._decode_modbus_response(temp_response)
                self._log_debug(f"Temperatura decodificada: {temp_value}")
            else:
                self._log_debug("No se recibió respuesta de temperatura")
            
            # Resultados
            result = {}
            if pressure_value is not None:
                result["pressure"] = pressure_value
            if temp_value is not None:
                result["temperature"] = temp_value
            
            if not result:
                return None
            
            self._log_debug(f"Lectura exitosa: {result}")
            return result
            
        except Exception as e:
            self._log_debug(f"Error: {str(e)}")
            return None
    
    def _send_rs485(self, data):
        """Envía comando por RS485 y recibe respuesta"""
        self.de_re.on()  # Modo transmisión
        self.uart.write(data)
        time.sleep_ms(10)  # Esperar transmisión
        self.de_re.off()  # Modo recepción
        time.sleep_ms(500)  # Esperar respuesta
        return self.uart.read()
    
    def _decode_modbus_response(self, response):
        """Decodifica respuesta Modbus a float"""
        if not response or len(response) < 7:
            return None
        
        # Extraer bytes del valor float (posiciones 3-6)
        float_bytes = response[3:7]
        
        try:
            # Convertir a float IEEE-754
            float_value = struct.unpack('>f', float_bytes)[0]
            return float_value
        except Exception as e:
            self._log_debug(f"Error decodificando float: {e}")
            return None
    
    def _log_debug(self, message):
        """Registra mensaje en archivo de log"""
        try:
            with open("rs485_simple_debug.txt", "a") as f:
                f.write(f"[{time.time()}] {message}\n")
        except:
            pass