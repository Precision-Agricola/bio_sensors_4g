import machine

def get_mac_suffix():
    mac = machine.unique_id()
    return ''.join('{:02x}'.format(b) for b in mac[-3:]).upper()

# Device identification (HTTP)
DEVICE_ID = f"ESP32_{get_mac_suffix()}"
