"""Base model for sensors digital and analogue with respective signal communication protocol"""
_sensor_registry = {}

def register_sensor(model, protocol):
    """Decorator for case-insensitive sensor registration"""
    def decorator(cls):
        key = (model.strip().upper(), protocol.strip().upper())
        _sensor_registry[key] = cls
        return cls
    return decorator

class Sensor:
    """Base class for all sensors with config management"""
    
    def __init__(self, name, model, protocol, vin, signal, **kwargs):
        self.name = name
        self.model = model.upper()
        self.protocol = protocol.upper()
        self.vin = float(vin)
        self.signal = signal
        self.config = kwargs  # Store all additional parameters
        
        # Common hardware initialization
        self._initialized = False
        self._init_hardware()

    def _init_hardware(self):
        """Basic hardware setup common to all sensors"""
        # Add any cross-protocol initialization here
        self._initialized = True

    def read(self):
        """
        Public read method with basic error handling
        Returns: dict of values or None
        """
        if not self._initialized:
            return None
            
        try:
            return self._read_implementation()
        except Exception as e:
            print(f"Error reading {self.name}: {str(e)}")
            return None

    def _read_implementation(self):
        """Sensor-specific read logic (MUST override)"""
        raise NotImplementedError("Subclasses must implement _read_implementation()")
