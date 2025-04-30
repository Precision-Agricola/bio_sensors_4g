import time
from calendar.rtc_manager import RTCManager
#TODO: changhe the import path (src.calendar.rtc_manager or calendar.rtc_manager)
rtc_manager = RTCManager()


if rtc_manager.rtc:
     rtc_manager.check_and_sync(threshold_seconds=180) # Umbral de 3 minutos

     while True:
         current_time = rtc_manager.get_formatted_time()
         if current_time:
             print(f"Hora actual del DS1302: {current_time}")
         else:
             print("No se pudo obtener la hora del DS1302.")
         time.sleep(10)
