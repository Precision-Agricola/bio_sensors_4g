# client/readings/analog_readings.py

from utils.logger import log_message

def read_analog_sensors():
    readings = {}

    # --- Sensor de pH ---
    try:
        from sensors.ph.ph_sensor import PHSensor
        ph_sensor = PHSensor()
        readings[ph_sensor.name] = ph_sensor.read()
    except Exception as e:
        log_message("Error leyendo sensor de pH", e)

    # --- Sensor de flujo YF-B1 ---
    try:
        from sensors.flow.flow import PulseFlowSensor
        flow_sensor = PulseFlowSensor(model="YF-B1")
        readings[flow_sensor.name] = flow_sensor.read()
    except Exception as e:
        log_message("Error leyendo sensor de flujo", e)

    if not readings:
        log_message("No se obtuvo lectura de sensores analógicos")

    # --- Agrega aquí más sensores analógicos manualmente ---
    # try:
    #     from sensors.abc.abc_sensor import ABCSensor
    #     abc_sensor = ABCSensor()
    #     readings[abc_sensor.name] = abc_sensor.read()
    # except Exception as e:
    #     log_message("Error leyendo sensor ABC", e)

    if not readings:
        log_message("No se obtuvo lectura de sensores analógicos")

    return readings
