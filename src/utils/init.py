# utils/init.py

import utime
import machine

try:
    from calendar.rtc_manager import RTCManager
    _RTC_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: No se pudo importar RTCManager: {e}. Sincronización RTC externa no disponible.")
    RTCManager = None
    _RTC_MANAGER_AVAILABLE = False

_rtc_manager_instance = None

def _get_rtc_manager_instance():
    global _rtc_manager_instance
    if not _RTC_MANAGER_AVAILABLE:
        return None
    if _rtc_manager_instance is None:
        _rtc_manager_instance = RTCManager()
        if not _rtc_manager_instance.rtc:
             _rtc_manager_instance = None
             print("ERROR: Falló la inicialización del hardware DS1302 en RTCManager.")
    return _rtc_manager_instance

def _fetch_time_from_external():
    rtc_man = _get_rtc_manager_instance()
    if rtc_man:
        time_tuple = rtc_man.get_time_tuple()
        if time_tuple and len(time_tuple) >= 6 and time_tuple[0] >= 2024:
            return time_tuple
        else:
            print(f"WARN: Hora de RTC externo inválida o muy antigua: {time_tuple}")
            return None
    return None

def _set_esp32_internal_rtc(time_tuple_ext):
    try:
        if not time_tuple_ext or len(time_tuple_ext) < 6:
            return False

        weekday = 0
        try:
            secs = utime.mktime(time_tuple_ext[0:6] + (0, 0))
            weekday = utime.localtime(secs)[6]
        except Exception as e:
            print(f"WARN: No se pudo calcular weekday exacto ({e}), usando Lunes(0).")

        rtc_tuple_for_internal = (time_tuple_ext[0], time_tuple_ext[1], time_tuple_ext[2], weekday,
                                  time_tuple_ext[3], time_tuple_ext[4], time_tuple_ext[5], 0) # microseg=0

        rtc_int = machine.RTC()
        rtc_int.datetime(rtc_tuple_for_internal)
        return True
    except Exception as e:
        print(f"ERROR: Fallo al configurar machine.RTC: {e}")
        return False

def initialize_internal_rtc():
    """Verifica el RTC interno y lo sincroniza desde el externo si es necesario."""
    try:
        current_internal_time = utime.localtime()

        if current_internal_time[0] < 2024:
            external_time_tuple = _fetch_time_from_external() # Leer DS1302

            if external_time_tuple:
                _set_esp32_internal_rtc(external_time_tuple)
            else:
                print("ERROR: No se pudo obtener hora válida de RTC externo. RTC interno sigue desconfigurado.")
        else:
            print("INFO: RTC interno ya parece tener hora válida.")

    except Exception as e:
        print(f"ERROR: Error crítico durante inicialización de RTC interno: {e}")
    print("INFO: --- Fin Inicialización RTC Interno ---")

def _format_datetime(dt_tuple):
    if not dt_tuple or len(dt_tuple) < 6: return "Fecha/Hora inválida"
    try: return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*dt_tuple[:6])
    except: return "Error de formato"

def system_setup():
    """Función principal para configurar el sistema al inicio."""
    print(f"Iniciando Setup del Sistema @ {_format_datetime(utime.localtime())}")
    initialize_internal_rtc()
    print("-----------------------------------")
    print("Setup del Sistema Completado.")
