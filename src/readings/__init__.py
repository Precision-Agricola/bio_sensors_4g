from readings.sensor_reader import SensorReader

# Crear una instancia global
reader = SensorReader()

# Función auxiliar
def read_sensors(relay='A', settling_time=None):
    return reader.read_sensors(relay, settling_time)