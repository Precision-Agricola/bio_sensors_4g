"""Sensor reading and data transmission code

Precisón Agrícola
Investigation and Development Department

@authors: Caleb De La Vara, Raúl Venegas, Eduardo Santos 
Feb 2025
Modified: March 2025 - Sistema de timer unificado

"""
from routines.aerator_3hr import turn_on_aerators
from config.config import _runtime_state


print("")
print("")
print("")
print("")
print("")
print("=====================")
print(f"Current runtime sate values: {_runtime_state}")

turn_on_aerators()

while True:
    pass
