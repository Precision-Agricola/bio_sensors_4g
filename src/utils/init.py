# utils/init.py

import utime
import machine
from utils.logger import log_message
from utils.logger import manage_log_file

try:
    from calendar.get_time import init_rtc as init_external_rtc
    from calendar.get_time import get_current_time as read_external_rtc
except ImportError as e:
    log_message(f"ERROR CRITICO: No se pudo importar init_external_rtc o read_external_rtc desde calendar.get_time: {e}")
    def read_external_rtc(rtc_obj): return None
    def init_external_rtc(): return None


def _fetch_time_from_source():
    try:
        rtc_ext = init_external_rtc()
        if rtc_ext:
            time_tuple_ext = read_external_rtc(rtc_ext)
            return time_tuple_ext
        else:
            log_message("Error al inicializar RTC externo (DS1302).")
            return None
    except Exception as e:
        log_message("Error al leer hora desde DS1302:", e)
        return None


def _set_esp32_rtc(time_tuple_ext):
    try:
        if not time_tuple_ext or len(time_tuple_ext) < 6:
             log_message("Error: Tupla de tiempo externa inválida para configurar RTC interno.")
             return False

        weekday = 0
        try:
             temp_tuple_for_mktime = time_tuple_ext[0:6] + (0, 0)
             timestamp = utime.mktime(temp_tuple_for_mktime)
             full_localtime_tuple = utime.localtime(timestamp)
             weekday = full_localtime_tuple[6]
        except Exception:
             log_message("Aviso: No se pudo calcular weekday exacto con mktime/localtime, usando Lunes(0).")

        rtc_tuple = (time_tuple_ext[0], time_tuple_ext[1], time_tuple_ext[2], weekday,
                     time_tuple_ext[3], time_tuple_ext[4], time_tuple_ext[5], 0)

        rtc_int = machine.RTC()
        rtc_int.datetime(rtc_tuple)
        return True
    except Exception as e:
        log_message("Error al configurar RTC interno (machine.RTC):", e)
        return False


def _initialize_rtc():
    try:
        current_internal_time = utime.localtime()
        if current_internal_time[0] < 2024:
            log_message("RTC interno parece no configurado. Intentando sincronizar...")
            external_time = _fetch_time_from_source()
            if external_time:
                if _set_esp32_rtc(external_time):
                    log_message("RTC interno configurado exitosamente.")
                    new_time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*utime.localtime()[:6])
                    log_message("Nueva hora RTC:", new_time_str)
                else:
                    log_message("Fallo al configurar RTC interno usando hora externa.")
            else:
                log_message("No se pudo obtener hora de fuente externa (DS1302/NTP).")
        else:
            current_time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*current_internal_time[:6])
            log_message("RTC interno ya tiene hora válida:", current_time_str)
    except Exception as e:
        log_message("Error crítico durante inicialización de RTC:", e)


def system_setup():
    manage_log_file()
    log_message("===================================")
    log_message("Iniciando Setup del Sistema...")
    log_message("===================================")
    _initialize_rtc()
    log_message("-----------------------------------")
    log_message("Setup del Sistema Completado.")
    log_message("-----------------------------------")
