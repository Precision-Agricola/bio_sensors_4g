from utils.logger import log_message

def read_rs485_sensors():
    from sensors.rs485.rs485_sensor import RS485Sensor
    try:
        sensor = RS485Sensor()
        readings = sensor.read()
        if not readings:
            log_message("No se obtuvo lectura de sensores RS485")
        return {"RS485": readings}
    except Exception as e:
        log_message("RS485 sensor read error", e)
        return {}

