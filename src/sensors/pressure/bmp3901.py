"""Pressure I2C sensor (BMP3901) usando micropython_bmpxxx"""
import time
from sensors.base import Sensor, register_sensor
from protocols.i2c import I2CDevice
from micropython_bmpxxx import bmpxxx

@register_sensor("BMP3901", "I2C")
class BMP3901Sensor(Sensor):
    def __init__(self, **config):
        self.config = config
        self.name = config.get("name", "BMP3901")
        self._initialized = False
        self.baseline = 0.0
        self.baseline_set = False
        self.sea_level_pressure = 1013.25  # Presión estándar a nivel del mar
        self._init_hardware()
        
    def _init_hardware(self):
        try:
            bus_num = self.config.get("bus_num", 0)
            addr = self.config.get("address", 0x77)
            scl_pin = self.config.get("scl_pin", 21)
            sda_pin = self.config.get("sda_pin", 23)
            
            # Obtener el objeto I2C
            i2c_obj = self.config.get("i2c_obj", None)
            
            if i2c_obj:
                # Usar un objeto I2C existente si se proporciona
                self.bmp = bmpxxx.BMP390(i2c=i2c_obj, address=addr)
            else:
                # Crear y usar nuestro propio dispositivo I2C
                self.i2c_device = I2CDevice(bus_num, addr, scl_pin=scl_pin, sda_pin=sda_pin)
                self.bmp = bmpxxx.BMP390(i2c=self.i2c_device.bus, address=addr)
            
            # Establecer presión a nivel del mar (opcional)
            custom_slp = self.config.get("sea_level_pressure")
            if custom_slp:
                self.bmp.sea_level_pressure = float(custom_slp)
                
            # Establecer altitud conocida (opcional)
            altitude = self.config.get("altitude")
            if altitude:
                self.bmp.altitude = float(altitude)
                
            self.calibrate_baseline()
            self._initialized = True
            print(f"BMP3901 inicializado. Presión al nivel del mar: {self.bmp.sea_level_pressure:.2f} hPa")
        except Exception as e:
            print(f"Error al inicializar BMP3901: {e}")
            self._initialized = False
        
    def read_pressure(self):
        """Lee la presión barométrica en hPa"""
        try:
            return self.bmp.pressure
        except Exception as e:
            print(f"Error al leer presión: {e}")
            return None
            
    def read_temperature(self):
        """Lee la temperatura en grados Celsius"""
        try:
            return self.bmp.temperature
        except Exception as e:
            print(f"Error al leer temperatura: {e}")
            return None
            
    def read_altitude(self):
        """Lee la altitud en metros basada en la presión al nivel del mar configurada"""
        try:
            return self.bmp.altitude
        except Exception as e:
            print(f"Error al leer altitud: {e}")
            return None
        
    def set_sea_level_pressure(self, pressure):
        """Establece la presión a nivel del mar para cálculos de altitud"""
        self.bmp.sea_level_pressure = pressure
        return self.bmp.sea_level_pressure
        
    def set_known_altitude(self, altitude):
        """Establece una altitud conocida para calibrar la presión a nivel del mar"""
        self.bmp.altitude = altitude
        return self.bmp.sea_level_pressure
            
    def detect_air_flow(self):
        """Detecta cambios en el flujo de aire basados en cambios de presión"""
        current = self.read_pressure()
        return (current is not None) and (abs(current - self.baseline) > 0.5)
        
    def calibrate_baseline(self):
        """Calibra la línea base de presión tomando múltiples lecturas"""
        if not self._initialized:
            return
            
        suma = 0.0
        readings = 0
        n = 5  # Menos lecturas para agilizar la inicialización
        
        for _ in range(n):
            p = self.read_pressure()
            if p is not None:
                suma += p
                readings += 1
            time.sleep(0.1)
            
        if readings > 0:
            self.baseline = suma / readings
            self.baseline_set = True
            print(f"Nueva línea base de presión: {self.baseline:.2f} hPa")
        else:
            print("No se pudo establecer la línea base de presión")
    
    # CORREGIDO: Método con nombre exactamente igual al esperado por la clase base
    def _read_implementation(self):
        """Implementación de lectura que devuelve todos los datos del sensor"""
        if not self._initialized:
            return None
            
        try:
            data = {
                "pressure": self.read_pressure(),
                "temperature": self.read_temperature(),
                "altitude": self.read_altitude(),
                "air_flow": self.detect_air_flow(),
                "sea_level_pressure": self.bmp.sea_level_pressure
            }
            return data
        except Exception as e:
            print(f"Error en _read_implementation: {e}")
            return None
