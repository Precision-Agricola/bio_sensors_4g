"""
Test runner module for BIO-IOT system
Allows running hardware tests individually or all at once
Precision Agrícola - Investigation and Development Department
March 2025
"""
from tests.hardware_test import (
    test_relays,
    test_rtc,
    test_analog_sensors,
    test_i2c_devices,
    run_hardware_tests
)

def run_relay_test():
    """Run only relay tests"""
    print("Running relay tests...")
    test_relays()
    print("Relay tests completed.")

def run_rtc_test():
    """Run only RTC tests"""
    print("Running RTC tests...")
    test_rtc()
    print("RTC tests completed.")

def run_sensor_tests():
    """Run only sensor tests"""
    print("Running sensor tests...")
    test_analog_sensors()
    test_i2c_devices()
    print("Sensor tests completed.")

def run_all_tests():
    """Run all hardware tests"""
    print("Running all hardware tests...")
    run_hardware_tests()
    print("All tests completed.")

# Menu for REPL usage
def show_menu():
    """Display interactive test menu in REPL"""
    print("\nBIO-IOT Hardware Test Menu")
    print("==========================")
    print("1. Test Relays")
    print("2. Test RTC")
    print("3. Test Sensors (Analog & I2C)")
    print("4. Run All Tests")
    print("0. Exit")
    
    choice = input("Enter choice (0-4): ")
    
    if choice == '1':
        run_relay_test()
    elif choice == '2':
        run_rtc_test()
    elif choice == '3':
        run_sensor_tests()
    elif choice == '4':
        run_all_tests()
    elif choice == '0':
        print("Exiting test menu")
        return False
    else:
        print("Invalid choice. Please try again.")
    
    return True

def interactive():
    """Start interactive menu"""
    print("Starting BIO-IOT test interface")
    menu_active = True
    while menu_active:
        menu_active = show_menu()
    print("Test interface closed")

# For direct execution
if __name__ == "__main__":
    interactive()
