"""
All Betting Systems Factory

Central module for loading all betting systems
"""

from pathlib import Path
import json


def get_system(system_name, config_dir='config'):
    """
    Get system instance by name
    
    Args:
        system_name: Name of the system (e.g., 'Home Win', 'O2.5 Back')
        config_dir: Path to config directory
    
    Returns:
        System instance
    """
    # Load portfolio stats
    config_path = Path(config_dir) / 'portfolio_stats.json'
    with open(config_path, 'r') as f:
        data = json.load(f)
        portfolio_stats = data['stats']
    
    # Import and initialize based on system name
    if system_name == 'Home Win':
        from systems.home_win_system import HomeWinSystem, get_home_win_config
        config = get_home_win_config(portfolio_stats)
        return HomeWinSystem(config)
    
    elif system_name == 'O2.5 Back':
        from systems.o25_back_system import O25BackSystem, get_o25_back_config
        config = get_o25_back_config(portfolio_stats)
        return O25BackSystem(config)
    
    elif system_name == 'O3.5 Lay':
        from systems.o35_lay_system import O35LaySystem, get_o35_lay_config
        config = get_o35_lay_config(portfolio_stats)
        return O35LaySystem(config)
    
    elif system_name == 'U1.5 Lay':
        from systems.u15_lay_system import U15LaySystem, get_u15_lay_config
        config = get_u15_lay_config(portfolio_stats)
        return U15LaySystem(config)
    
    elif system_name == 'FHGU0.5 Lay':
        from systems.fhgu05_lay_system import FHGU05LaySystem, get_fhgu05_lay_config
        config = get_fhgu05_lay_config(portfolio_stats)
        return FHGU05LaySystem(config)
    
    else:
        raise ValueError(f"Unknown system: {system_name}")


def get_all_systems(config_dir='config'):
    """
    Get all system instances
    
    Returns:
        Dict of {system_name: system_instance}
    """
    system_names = [
        'Home Win',
        'O2.5 Back',
        'O3.5 Lay',
        'U1.5 Lay',
        'FHGU0.5 Lay'
    ]
    
    return {name: get_system(name, config_dir) for name in system_names}
