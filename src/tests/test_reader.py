from readings.sensor_reader import SensorReader

def main():
    # Crear el lector de sensores con un tiempo de asentamiento reducido para pruebas
    reader = SensorReader(settling_time=5)  # Solo 5 segundos para pruebas
    
    print("=== TEST DE LECTURA DE SENSORES ===")
    
    # Test 1: Leer sensores en relé A
    print("\nTest 1: Leyendo sensores en relé A")
    readings_a = reader.read_sensors(relay='A')
    print("Resultados relé A:", readings_a)
    
    # Esperar un poco entre pruebas
    print("\nEsperando 2 segundos...")
    time.sleep(2)
    
    # Test 2: Leer sensores en relé B
    print("\nTest 2: Leyendo sensores en relé B")
    readings_b = reader.read_sensors(relay='B')
    print("Resultados relé B:", readings_b)
    
    # Test 3: Obtener últimas lecturas sin activar sensores
    print("\nTest 3: Obteniendo últimas lecturas (sin activar sensores)")
    last_readings = reader.get_last_readings()
    print("Últimas lecturas:", last_readings)
    
    print("\n=== PRUEBAS COMPLETADAS ===")

if __name__ == "__main__":
    main()
