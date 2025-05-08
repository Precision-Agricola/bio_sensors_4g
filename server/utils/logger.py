import uos
import utime

LOG_FILENAME = 'app.log'
MAX_LOG_SIZE_BYTES = 200 * 1024
LOGGING_ENABLED = True

def _get_timestamp():
    try:
        t = utime.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
    except Exception:
        return "NO_RTC_TIME"

def log_message(*args):
    if not LOGGING_ENABLED:
        return
    try:
        manage_log_file()
        message_parts = []
        for arg in args:
            message_parts.append(str(arg))
        message = ' '.join(message_parts)
        timestamp = _get_timestamp()
        log_entry = f"{timestamp} {message}\n"
        print(log_entry)  
        with open(LOG_FILENAME, 'a') as f:
            f.write(log_entry)

    except Exception as e:
        print("!!! LOGGING FAILED !!!")
        print("Original log args:", args)
        print("Error:", e)

def manage_log_file():
    if not LOGGING_ENABLED:
        return
    try:
        stat_info = uos.stat(LOG_FILENAME)
        file_size = stat_info[6]
        if file_size > MAX_LOG_SIZE_BYTES:
            print(f"Log file '{LOG_FILENAME}' size ({file_size} bytes) exceeds limit ({MAX_LOG_SIZE_BYTES} bytes). Rotating (deleting old).")
            uos.remove(LOG_FILENAME)
            if LOGGING_ENABLED:
                 log_message(f"Log file rotated (deleted) due to size limit ({MAX_LOG_SIZE_BYTES} bytes).")

    except OSError as e:
        if e.args[0] == 2:
            pass
        else:
            print(f"Error managing log file '{LOG_FILENAME}': {e}")
    except Exception as e:
        print(f"Unexpected error during log management: {e}")
