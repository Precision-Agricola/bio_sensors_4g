"""Base model for sensor reading"""

class SensorBase:
    """Base class for all sensors"""
    def __init__(self, name: str, pin:int = None):
        """Builder"""
        self.name = name
        self.pin = pin
        self.connected = False
        self.last_reading = None

    def initialize(self):
        """Initialize the sensor hardware -- override in child classes"""
        raise NotImplementedError

    def read(self):
        """Read the data from he sensor -- override in child classes"""
        raise NotImplementedError

    def get_reading(self):
        """Get sensor reading with error handling"""

        try:
            if not self.connected:
                 return None
            self.last_reading = self.read()
        except Exception as e:
            print(f"Error reading {self.name}: {str(e)}")
            return None

