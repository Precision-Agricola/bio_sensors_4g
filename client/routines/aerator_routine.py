# client/routines/aerator_routine.py

from system.control.relays import LoadRelay
import config.runtime as runtime_config
import time
from utils.logger import log_message

def turn_on_aerators(wdt=None):
    log_message("Initializing aerator routine with persistent config...")

    tf = runtime_config.get_speed()
    cycle_hours = runtime_config.get_cycle_duration()
    duty = runtime_config.get_duty_cycle()

    total_cycle = int(cycle_hours * 3600) // tf
    on_time = int(total_cycle * duty)
    off_time = total_cycle - on_time

    relays = LoadRelay()
    idx = 0

    log_message(f"Ciclo total: {cycle_hours}h ({total_cycle}s) | Duty: {duty*100:.1f}%")
    log_message(f"ON: {on_time}s | OFF: {off_time}s | Velocidad: x{tf}")

    try:
        while True:
            log_message(f"Aerador {idx} ON")
            relays.turn_on(idx)
            _wait(on_time, wdt)

            relays.turn_off(idx)
            log_message(f"Aerador {idx} OFF")
            _wait(off_time, wdt)

            idx = 1 - idx
    except Exception as e:
        log_message(f"Error en rutina de aeradores: {e}")
        relays.turn_off()

def _wait(secs, wdt=None):
    t0 = time.time()
    while time.time() - t0 < secs:
        if wdt: wdt.feed()
        time.sleep(1)
 