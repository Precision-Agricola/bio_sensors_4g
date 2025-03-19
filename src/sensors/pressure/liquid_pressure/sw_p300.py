"""Liquid Pressure Sensor SW-P300 using RS485/Modbus"""
from sensors.base import Sensor, register_sensor
from protocols.rs485 import RS485Device
from config.config import RS485_TX_PIN, RS485_RX_PIN, RS485_DE_RE_PIN
import time

@register_sensor("SW-P300", "RS485")
class SWP300Sensor(Sensor):
    def __init__(self, name, model, protocol, vin, uart_id=2, commands=None, **kwargs):
        if 'signal' not in kwargs:
            kwargs['signal'] = 0
        self.uart_id = uart_id
        self.commands = commands or {
            "pressure": b'\x01\x03\x04\x0a\x00\x02\xE5\x39',
            "temperature": b'\x01\x03\x04\x0c\x00\x02\x05\x38',
            "ambient_temperature": b'\x01\x03\x04\x0c\x00\x02\x05\x38'
        }
        
        super().__init__(name, model, protocol, vin, **kwargs)
    
    def _init_hardware(self):
        """Inicializa el hardware del sensor."""
        super()._init_hardware()
        self.rs485 = RS485Device(
            uart_id=self.uart_id,
            baudrate=9600,
            tx_pin=RS485_TX_PIN,
            rx_pin=RS485_RX_PIN,
            de_re_pin=RS485_DE_RE_PIN
        )
        self._initialized = True
    
    def _read_implementation(self):
        """
        Implementación de la lectura del sensor.
        
        Returns:
            dict: Diccionario con los valores leídos o None si hay error
        """
        try:
            if not hasattr(self, 'rs485') or not self._initialized:
                self._init_hardware()
            
            # TODO: avoid reading the sensor one by one 
            pressure_response = self.rs485.send_command(self.commands["pressure"])
            pressure_value = None
            if pressure_response:
                pressure_value = self.rs485.decode_modbus_response(pressure_response)

            temp_response = self.rs485.send_command(self.commands["temperature"])
            temp_value = None
            if temp_response:
                temp_value = self.rs485.decode_modbus_response(temp_response)
            

            ambient_response = self.rs485.send_command(self.commands["ambient_temperature"])
            ambient_value = None
            if ambient_response:
                ambient_value = self.rs485.decode_modbus_response(ambient_response)

            time.sleep(2)

            result = {}
            if pressure_value is not None:
                result["pressure"] = pressure_value
            if temp_value is not None:
                result["temperature"] = temp_value
            if ambient_value is not None:
                result["ambient_temperature"] = ambient_value
                
            if not result:
                return None
                
            return result
            
        except Exception as e:
            print(f"Error en lectura del sensor {self.name}: {str(e)}")
            return None
