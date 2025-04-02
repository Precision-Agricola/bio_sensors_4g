"""System log file"""
import os

LOG_FILE = "data/log.txt"
MAX_LOG_SIZE = 1024 * 300  # 300 KB limit

def print_to_log(*args):
    """Append a log message to the system log file rotating with 300KB limit."""
    msg = " ".join(map(str, args)) + "\n"
    try:
        if os.path.exists(LOG_FILE):
            if os.stat(LOG_FILE).st_size > MAX_LOG_SIZE:
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("")
    except OSError:
        pass
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg)
