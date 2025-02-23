import time
from machine import Pin, I2C
from utils.micropython_bmpxxx import bmpxxx
relay1 = Pin(14, Pin.OUT)
relay2 = Pin(13, Pin.OUT)

relay1.value(1)
relay2.value(1)
time.sleep(1)

i2c = I2C(scl=Pin(23), sda=Pin(21))
devices = i2c.scan()
if devices:
    for d in devices:
        print(f"I2C device at address: {hex(d)}")
else:
    print("ERROR: No I2C devices found")
print("")

bmp = bmpxxx.BMP390(i2c=i2c, address=0x77)

print(f"Initial sea level pressure = {bmp.sea_level_pressure:.2f} hPa")
bmp.sea_level_pressure = 1017.0
print(f"Adjusted sea level pressure = {bmp.sea_level_pressure:.2f} hPa")

bmp.altitude = 111.0
print(f"Adjusted SLP using altitude {bmp.altitude:.2f} m = {bmp.sea_level_pressure:.2f} hPa\n")

while True:
    print(f"Pressure = {bmp.pressure:.2f} hPa")
    print(f"Temperature = {bmp.temperature:.2f} °C")
    
    meters = bmp.altitude
    print(f"Altitude = {meters:.2f} m")
    feet = meters * 3.28084
    feet_int = int(feet)
    inches = int((feet - feet_int) * 12)
    print(f"Altitude = {feet_int} ft {inches} in")
    
    time.sleep(2.5)
