import time

def setup_logger():
    class Logger:
        def info(self, msg):
            print(f"[INFO {time.ticks_ms()}] {msg}")
            
        def error(self, msg):
            print(f"[ERROR {time.ticks_ms()}] {msg}")
            
        def warning(self, msg):
            print(f"[WARN {time.ticks_ms()}] {msg}")
    
    return Logger()

logger = setup_logger()
