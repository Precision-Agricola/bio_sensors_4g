# broker/core/__init__.py
# Core module initialization

def init():
    """Initialize all core modules"""
    # Import all modules to ensure initialization
    import core.access_point
    import core.http_server
    import core.aws_forwarding
    import core.data_handler
    import core.stats
    
    print("Core modules initialized")

