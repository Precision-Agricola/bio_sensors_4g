import uasyncio as asyncio
import time
from machine import Pin
import config.runtime as runtime_config
import config.config as app_config
from utils.logger import log_message

class Relay:
    def __init__(self, pin_num, active_high=True):
        self._pin = Pin(pin_num, Pin.OUT, value=0 if active_high else 1)
        self._ah = active_high
        self._on = False

    def toggle(self):
        self._on = not self._on
        if self._on:
            self._pin.value(1 if self._ah else 0)
        else:
            self._pin.value(0 if self._ah else 1)

    def is_on(self):
        return self._on

async def monitor_switch():
    time_factor = runtime_config.get_speed()
    interval_min = runtime_config.get_pump_interval()
    duration_min = runtime_config.get_pump_duration()
    
    intervalo_seg = (interval_min * 60) // time_factor
    duracion_seg = (duration_min * 60) // time_factor
    
    log_message(f"Pump Control iniciado. Intervalo: {intervalo_seg}s, Duración: {duracion_seg}s")

    button = Pin(app_config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    pump = Relay(app_config.RECIRCULATION_POMP_PIN)
    
    last_button_state = button.value()
    pump_on_by_auto = False
    next_auto_on_time = time.ticks_add(time.ticks_ms(), intervalo_seg * 1000)

    while True:
        current_state = button.value()
        if current_state != last_button_state and current_state == 0:
            await asyncio.sleep_ms(50)
            if button.value() == 0:
                log_message("Botón manual presionado.")
                pump.toggle()
                pump_on_by_auto = False
                next_auto_on_time = time.ticks_add(time.ticks_ms(), intervalo_seg * 1000)
        
        last_button_state = current_state

        if time.ticks_diff(time.ticks_ms(), next_auto_on_time) > 0:
            if not pump.is_on():
                log_message(f"Ciclo automático: Encendiendo bomba por {duracion_seg}s.")
                pump.toggle()
                pump_on_by_auto = True
                auto_off_time = time.ticks_add(time.ticks_ms(), duracion_seg * 1000)
            
            next_auto_on_time = time.ticks_add(time.ticks_ms(), intervalo_seg * 1000)

        if pump_on_by_auto and time.ticks_diff(time.ticks_ms(), auto_off_time) > 0:
            if pump.is_on():
                log_message("Ciclo automático: Apagando bomba.")
                pump.toggle()
            pump_on_by_auto = False

        await asyncio.sleep_ms(50)
