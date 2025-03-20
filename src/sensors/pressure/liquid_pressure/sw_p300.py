"""SW_P300 Liquid Pressure Sensor using RS485"""
import time
from protocols.rs485 import init_rs485

class SW_P300:
    """Simple RS485-based pressure sensor implementation"""
    
    def __init__(self, name="SWP300"):
        """Initialize the pressure sensor"""
        self.name = name
        self._initialized = False
        self.device = None
        self.log_file = "sensor_log.txt"
        
        # Comandos predefinidos que ya funcionan
        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',
            b'\x01\x03\x04\x08\x00\x02\x44\xF9',
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'
        ]
        
        try:
            # Usar los mismos pines y configuración que ya funcionan
            self.device = init_rs485(uart_id=2, baudrate=9600, tx_pin=1, rx_pin=3, de_re_pin=22)
            self._initialized = True
            self._log("Sensor inicializado")
        except Exception as e:
            self._log(f"ERROR: Inicialización fallida: {str(e)}")
    
    def read(self):
        """Read all sensor values and return them as a dictionary"""
        if not self._initialized or not self.device:
            return None
            
        readings = {}
        all_readings_ok = True
        
        for i, cmd in enumerate(self.commands):
            try:
                resp = self.device.send_command(cmd)
                if resp:
                    val = self.device.ieee754_to_float(resp[3:7])
                    param_name = f"param_{i+1}"
                    readings[param_name] = val
                    self._log(f"OK: {param_name}={val}")
                else:
                    all_readings_ok = False
                    self._log(f"ERROR: No response for CMD:{cmd.hex()}")
            except Exception as e:
                all_readings_ok = False
                self._log(f"ERROR: Exception reading sensor: {str(e)}")
        
        return readings if readings else None
    
    def _log(self, message):
        """Log message to file without using print"""
        try:
            with open(self.log_file, "a") as f:
                f.write(f"{time.time()} {message}\n")
        except:
            pass  # Silent fail if logging fails
