# server/core/device_info.py
import machine

def get_mac_suffix():
    mac = machine.unique_id()
    return ''.join('{:02x}'.format(b) for b in mac[-3:]).upper()

DEVICE_ID = f"SERVER_{get_mac_suffix()}"
