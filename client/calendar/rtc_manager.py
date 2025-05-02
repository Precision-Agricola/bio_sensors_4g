# src/calendar/rtc_manager.py

from machine import Pin
from utils.logger import log_message
import time
try:
    import calendar.ds1302 as ds1302
except ImportError:
    log_message("ERROR: No se encontró el módulo 'calendar.ds1302'.")
    ds1302 = None

try:
    from config.config import RTC_CLK_PIN, RTC_DIO_PIN, RTC_CS_PIN
    log_message("INFO: Pines RTC cargados desde config.config.")
except ImportError:
    log_message("WARN: RTC Pins no en config.config, usando defaults 16 (CLK), 21 (DIO), 23 (CS).")
    RTC_CLK_PIN = 16
    RTC_DIO_PIN = 21
    RTC_CS_PIN = 23

def _format_datetime(dt_tuple):
    if not dt_tuple: return None
    try:
        if len(dt_tuple) >= 7: # Asume (Y, M, D, WD, H, M, S)
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                dt_tuple[0], dt_tuple[1], dt_tuple[2], dt_tuple[4], dt_tuple[5], dt_tuple[6])
        else:
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*dt_tuple[:6])
    except (IndexError, TypeError):
         return None

def _compute_weekday(day, month, year):
    if month < 3: month += 12; year -= 1
    K = year % 100; J = year // 100
    h = (day + (13 * (month + 1)) // 5 + K + K // 4 + J // 4 + 5 * J) % 7
    return ((h + 5) % 7) + 1

class RTCManager:
    def __init__(self):
        self.rtc = None
        if ds1302 is None: return
        try:
            clk = Pin(RTC_CLK_PIN, Pin.OUT)
            dio = Pin(RTC_DIO_PIN)
            cs = Pin(RTC_CS_PIN, Pin.OUT)
            self.rtc = ds1302.DS1302(clk, dio, cs)
            _ = self.rtc.year()
            log_message("INFO: RTCManager inicializado correctamente.")
        except Exception as e:
            log_message(f"ERROR CRITICO inicializando DS1302: {e}")
            self.rtc = None

    def set_time_from_string(self, time_str):
        if not self.rtc: return log_message("ERROR: RTCManager no inicializado.")
        try:
            date_part, time_part = time_str.split(' ')
            day, month, year = map(int, date_part.split('/'))
            hour, minute = map(int, time_part.split(':'))
            weekday = _compute_weekday(day, month, year)
            dt = (year, month, day, weekday, hour, minute, 0)
            self.rtc.date_time(dt)
            log_message(f"INFO: RTC set (string) to: {_format_datetime(dt)}")
        except Exception as e:
            log_message(f"ERROR: Fallo en set_time_from_string: {e}")

    def set_time_from_localtime(self, time_tuple=None):
        if not self.rtc: return log_message("ERROR: RTCManager no inicializado.")
        try:
            if time_tuple is None: time_tuple = time.localtime()
            weekday_ds = time_tuple[6] + 1
            dt = (time_tuple[0], time_tuple[1], time_tuple[2], weekday_ds,
                  time_tuple[3], time_tuple[4], time_tuple[5])
            self.rtc.date_time(dt) # Envía la tupla al DS1302
            log_message(f"INFO: RTC set (localtime) to: {_format_datetime(dt)}")
        except Exception as e:
            log_message(f"ERROR: Fallo en set_time_from_localtime: {e}")

    def get_time_tuple(self):
        if not self.rtc: return None
        try:
            return (self.rtc.year(), self.rtc.month(), self.rtc.day(),
                    self.rtc.hour(), self.rtc.minute(), self.rtc.second())
        except Exception as e:
             log_message(f"ERROR: Fallo en get_time_tuple: {e}")
             return None

    def get_formatted_time(self):
        return _format_datetime(self.get_time_tuple())

    def check_and_sync(self, threshold_seconds=120):
        if not self.rtc: 
            log_message("ERROR: RTCManager no inicializado.")
            return False
        sync_performed = False
        try:
            now_internal = time.localtime()
            now_external = self.get_time_tuple()
            log_message(f"DEBUG: Check/Sync - Interno={_format_datetime(now_internal)}")
            if now_external is None:
                log_message("WARN: Check/Sync - No se pudo leer RTC externo. Intentando sincronizar.")
                needs_sync = True
            else:
                log_message(f"DEBUG: Check/Sync - Externo={_format_datetime(now_external)}")
                synced = False
                try:
                    secs_internal = time.mktime(now_internal)
                    secs_external = time.mktime(now_external + (now_internal[6], now_internal[7]))
                    diff = abs(secs_internal - secs_external)
                    log_message(f"DEBUG: Check/Sync - Diferencia={diff}s (Umbral={threshold_seconds}s)")
                    synced = diff <= threshold_seconds
                except Exception as e:
                     log_message(f"WARN: Check/Sync - mktime falló ({e}). Usando chequeo simple (Minutos).")
                     minute_diff_threshold = (threshold_seconds // 60) + 1
                     synced = (now_internal[0] == now_external[0] and
                               now_internal[1] == now_external[1] and
                               now_internal[2] == now_external[2] and
                               now_internal[3] == now_external[3] and
                               abs(now_internal[4] - now_external[4]) <= minute_diff_threshold)
                needs_sync = not synced

            if needs_sync:
                log_message("INFO: Check/Sync - Estado=Desincronizado. Sincronizando RTC externo...")
                self.set_time_from_localtime(now_internal)
                sync_performed = True
                time.sleep(0.5) # Pausa breve
                log_message(f"INFO: Check/Sync - Externo Post-Sync={self.get_formatted_time()}")
            else:
                log_message("INFO: Check/Sync - Estado=Sincronizado.")

        except Exception as e:
            log_message(f"ERROR: Fallo en check_and_sync: {e}")
        return sync_performed
