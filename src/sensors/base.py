"""Base model for sensors digital and analogue with respective signal communication protocol"""
_sensor_registry = {}


def register_sensor(model, protocol):
    """Decorator"""
    def decorator(cls):
        _sensor_registry[(model, protocol)] = cls
        return cls
    return decorator

class Sensor:
    """Base model"""
    def __init__(self, name, model, protocol, vin, signal, **kwargs):
        self.name = name
        self.model = model
        self.protocol = protocol
        self.vin = vin
        self.signal = signal
        
    def read(self):
        """Every sensor should implement its own reading method"""
        raise NotImplementedError("Subclasses must implement _read()_ method")

