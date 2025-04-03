"""MicroPython system logger with log rotation at 300KB."""

import os

LOG_FILE = "data/log.txt"
MAX_LOG_SIZE = 1024 * 300  # 300 KB

def print_to_log(*args):
    """
    Append a message to the system log file.

    If the log file exceeds MAX_LOG_SIZE, it will be cleared before writing.
    Accepts multiple arguments which are joined into a single line.
    """
    msg = " ".join(map(str, args)) + "\n"
    try:
        size = 0
        try:
            with open(LOG_FILE, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
        except OSError:
            pass  # File doesn't exist yet

        if size > MAX_LOG_SIZE:
            with open(LOG_FILE, "w") as f:
                f.write("")

        with open(LOG_FILE, "a") as f:
            f.write(msg)
    except OSError:
        pass
