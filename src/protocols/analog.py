""" Analog Protocol Handler"""

class AnalogInput:
    def __init__(self, pin):
        from machine import ADC, Pin
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)  # Full 3.3V range

    def read(self):
        return self.adc.read()
