"""
lib/__init__.py
Denon AVR-X2300W control library module

This module provides functions to control a Denon AVR-X2300W receiver
via its HTTP API interface. All control functions are organized in this
library for easy import and use throughout the project.
"""

import logging

# Import all control functions
from .power_on import power_on
from .power_off import power_off

# Configure module logger
logger = logging.getLogger(__name__)
logger.debug("Initializing Denon AVR control library")

# Module metadata
__version__ = '1.0.0'
__description__ = 'Denon AVR-X2300W HTTP API Control Library'

# List of all exported functions
__all__ = [
    'power_on',
    'power_off',
    # Future functions to be added:
    # 'get_status',
    # 'set_volume',
    # 'change_input',
    # 'mute_toggle',
    # 'get_device_info',
]

# Log successful module initialization
logger.debug(f"Denon AVR control library v{__version__} initialized successfully")
logger.debug(f"Available functions: {', '.join(__all__)}")