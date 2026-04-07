"""
All Systems - Factory for Creating System Instances

CRITICAL FIX: Uses only BaseSystem class which has correct buffer validation.
Individual system files (u15_lay_system.py, etc.) have bugs and should not be used.

This file creates all system instances using the correct BaseSystem implementation.
"""

try:
    from systems.base_system import BaseSystem
except ImportError:
    from base_system import BaseSystem


class HomeWinSystem(BaseSystem):
    """Home Win betting system"""
    
    def __init__(self, config_dir='config'):
        super().__init__('Home Win', config_dir)
    
    def get_system_info(self):
        return {
            'name': self.system_name,
            'description': 'Back home team to win',
            'bet_type': 'back',
            'market': 'Match Odds - Home'
        }


class O25BackSystem(BaseSystem):
    """Over 2.5 Goals Back betting system"""
    
    def __init__(self, config_dir='config'):
        super().__init__('O2.5 Back', config_dir)
    
    def get_system_info(self):
        return {
            'name': self.system_name,
            'description': 'Back over 2.5 goals',
            'bet_type': 'back',
            'market': 'Over/Under 2.5 Goals'
        }


class O35LaySystem(BaseSystem):
    """Over 3.5 Goals Lay betting system"""
    
    def __init__(self, config_dir='config'):
        super().__init__('O3.5 Lay', config_dir)
    
    def get_system_info(self):
        return {
            'name': self.system_name,
            'description': 'Lay over 3.5 goals (bet against high scoring)',
            'bet_type': 'lay',
            'market': 'Over/Under 3.5 Goals'
        }


class U15LaySystem(BaseSystem):
    """Under 1.5 Goals Lay betting system"""
    
    def __init__(self, config_dir='config'):
        super().__init__('U1.5 Lay', config_dir)
    
    def get_system_info(self):
        return {
            'name': self.system_name,
            'description': 'Lay under 1.5 goals (bet on 2+ goals)',
            'bet_type': 'lay',
            'market': 'Over/Under 1.5 Goals'
        }


class FHGU05LaySystem(BaseSystem):
    """First Half Goals Under 0.5 Lay betting system"""
    
    def __init__(self, config_dir='config'):
        super().__init__('FHGU0.5 Lay', config_dir)
    
    def get_system_info(self):
        return {
            'name': self.system_name,
            'description': 'Lay first half under 0.5 goals (bet on first half goal)',
            'bet_type': 'lay',
            'market': 'First Half Goals Under 0.5'
        }


def get_system(system_name, config_dir='config'):
    """
    Factory function to get a system instance
    
    Args:
        system_name: Name of the system
        config_dir: Configuration directory
        
    Returns:
        System instance
    """
    systems = {
        'Home Win': HomeWinSystem,
        'O2.5 Back': O25BackSystem,
        'O3.5 Lay': O35LaySystem,
        'U1.5 Lay': U15LaySystem,
        'FHGU0.5 Lay': FHGU05LaySystem
    }
    
    if system_name not in systems:
        raise ValueError(f"Unknown system: {system_name}")
    
    return systems[system_name](config_dir)


def get_all_systems(config_dir='config'):
    """
    Get all system instances
    
    Args:
        config_dir: Configuration directory
        
    Returns:
        dict: Dictionary of system_name -> system_instance
    """
    return {
        'Home Win': HomeWinSystem(config_dir),
        'O2.5 Back': O25BackSystem(config_dir),
        'O3.5 Lay': O35LaySystem(config_dir),
        'U1.5 Lay': U15LaySystem(config_dir),
        'FHGU0.5 Lay': FHGU05LaySystem(config_dir)
    }
