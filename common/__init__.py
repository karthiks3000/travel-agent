"""
Common utilities shared across travel agents
"""

__version__ = "0.1.0"

# Optional import - only available when nova_act is installed
try:
    from .browser_wrapper import BrowserWrapper
    __all__ = ["BrowserWrapper"]
except ImportError:
    # BrowserWrapper not available - this is fine for demos and testing
    __all__ = []
