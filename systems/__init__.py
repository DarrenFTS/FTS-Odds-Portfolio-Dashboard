"""
Betting Systems Package

This package contains all betting system implementations.
"""

# Import the factory function
from systems.all_systems import get_system, get_all_systems

# Don't import individual system classes here to avoid circular imports
# They are loaded dynamically through get_system()

__all__ = ['get_system', 'get_all_systems']
