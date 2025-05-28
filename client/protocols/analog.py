# client/protocols/analog.py

class AnalogInput:
    def __init__(self, pin):
        from machine import ADC, Pin
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)

    def read(self):
        return self.adc.read()
