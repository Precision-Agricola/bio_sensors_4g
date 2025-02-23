from machine import Timer, Pin, ADC, I2C
from calendar.get_time import init_rtc, get_current_time
from utils.micropython_bmpxxx import bmpxxx
import time

relay1 = Pin(13, Pin.OUT)
relay2 = Pin(14, Pin.OUT)

adc36 = ADC(Pin(36))
adc39 = ADC(Pin(39))

rtc = init_rtc()

# Inicializá el bus I2C, pero no el sensor
i2c = None
bmp = None  # Se creará tras energizar

def sensor_routine():
    global bmp
    try:
        # Energiza relevadores
        relay1.value(1)
        relay2.value(1)
        time.sleep(1)  # Esperar estabilización
        if i2c is None:
            try:
                i2c = I2C(scl=Pin(21), sda=Pin(23))
            except Exception as e:
                print(f"No se pudo inicializar el bus I2C: {e}")
                # Podés desenergizar si falla
                relay1.value(0)
                relay2.value(0)
                return
        # Si no existe la instancia, se crea
        if bmp is None:
            try:
                temp_bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)
                temp_bmp.sea_level_pressure = 1013.25
                bmp = temp_bmp
            except Exception as e:
                print(f"No se pudo inicializar BMP390: {e}")
                # Podés desenergizar si falla
                relay1.value(0)
                relay2.value(0)
                return

        # Leer analógicos
        val_36 = adc36.read()
        val_39 = adc39.read()

        # Leer presión / temperatura
        pressure = bmp.pressure
        temperature = bmp.temperature

        # Mostrar
        print(f"ADC36={val_36}, ADC39={val_39}, Presion={pressure:.2f}, Temp={temperature:.2f}")

        # Desenergiza relevadores
        relay1.value(0)
        relay2.value(0)

    except Exception as e:
        print(f"Error rutina de sensores: {e}")

def check_time(timer):
    y, mo, d, h, m, s = get_current_time(rtc)
    if s == 10:
        print(f"Iniciando Rutina a la hora: {h}:{m}:{s}")
        sensor_routine()

t = Timer(0)
t.init(period=1000, mode=Timer.PERIODIC, callback=check_time)

