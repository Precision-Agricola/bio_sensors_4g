# boot.py - runs on boot-up
from machine import Pin
import time
import uos, esp

# Boot mode detection
boot_pin = Pin(25, Pin.IN, Pin.PULL_DOWN)

def display_boot_banner(mode):
    print(f"""
╔═══════════════════════════════════════════════╗
║                                               ║
║      PRECISIÓN AGRÍCOLA - BIO-IOT             ║ 
║                                               ║
║        --- {mode} ---                   ║
║      Pin Configuration: GPIO25 - {"1" if mode == "Sensing Mode" else "0"}            ║
║                                               ║ 
║       **                                      ║
║      *****.                                   ║
║    *********,                                 ║
║   ************                                ║
║  **************    (((((((((#                 ║
║  ***********   (((((((((((###                 ║
║ **********  (((((((((((######                 ║
║ ********   ((((((((((#######                  ║
║  ******  ((((((((((########*                  ║
║   *****  (((((((##########                    ║
║    ***  ((((((##########                      ║
║      *  ((((##########                        ║
║         (########.                            ║
║                                               ║
╚═══════════════════════════════════════════════╝
""")

if boot_pin.value():
    # Sensing Mode
    display_boot_banner("Sensing Mode")
    print("Working mode")
    print("Disabling UART-REPL-OSDEBUG")
    
    # Disable debug output and REPL
    uos.dupterm(None, 0)   # Disable REPL on UART0
    esp.osdebug(None)      # Disable boot messages
    
    # The rest will be handled by main.py
else:
    # Programming Mode
    display_boot_banner("Programmable Mode")
    print("Flashing mode")
    print("REPL-UART0 Free to use")
    # Keep REPL enabled for programming