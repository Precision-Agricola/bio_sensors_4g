# broker/core/__init__.py
# Core module initialization
from utils.logger import log_message

def init():
    """Initialize all core modules"""
    import core.access_point
    import core.aws_forwarding
    import core.data_handler
    import core.stats
    
    log_message("Core modules initialized")

