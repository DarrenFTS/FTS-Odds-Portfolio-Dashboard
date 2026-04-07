"""
Base Betting System

Base class that all betting systems inherit from.
Provides common functionality for:
- Loading configurations
- Checking odds ranges and buffers
- Applying filters
- Generating bet signals

CRITICAL FIX: Strict buffer range validation to prevent bets outside configured ranges
"""

import json
from pathlib import Path
import pandas as pd


class BaseSystem:
    """Base class for all betting systems"""
    
    def __init__(self, system_name, config_dir='config'):
        """
        Initialize the betting system
        
        Args:
            system_name: Name of the system (e.g., 'O2.5 Back')
            config_dir: Directory containing configuration files
        """
        self.system_name = system_name
        self.config_dir = Path(config_dir)
        self.config = self._load_config()
        self.market_column = self.config['market_column']
        self.has_filter = self.config['has_filter']
        self.filter_condition = self.config.get('filter_condition')
        self.filter_buffer_min = self.config.get('filter_buffer_min')
        self.configurations = self.config['configurations']
    
    def _load_config(self):
        """Load system configuration from JSON"""
        config_file = self.config_dir / 'systems_config.json'
        with open(config_file, 'r') as f:
            all_configs = json.load(f)
        
        if self.system_name not in all_configs:
            raise ValueError(f"System '{self.system_name}' not found in configuration")
        
        return all_configs[self.system_name]
    
    def get_config_for_league(self, league):
        """
        Get configuration for a specific league
        
        Args:
            league: League name
            
        Returns:
            dict: Configuration with exact_min, exact_max, buffer_min, buffer_max
        """
        for config in self.configurations:
            if config['league'] == league:
                return config
        return None
    
    def is_in_exact_range(self, odds, config):
        """
        Check if odds are in the exact range
        
        CRITICAL: Uses <= to ensure boundary values are included
        """
        return config['exact_min'] <= odds <= config['exact_max']
    
    def is_in_buffer(self, odds, config):
        """
        Check if odds are in the buffer zone (including exact range)
        
        CRITICAL FIX: This is the key validation that prevents invalid bets
        
        Returns True if:
            buffer_min <= odds <= buffer_max
        
        Returns False if:
            odds < buffer_min OR odds > buffer_max
        
        Examples:
            buffer_min=4.00, buffer_max=5.10
            - odds=4.00 -> True (at minimum)
            - odds=5.10 -> True (at maximum)
            - odds=5.20 -> False (ABOVE maximum)
            - odds=3.90 -> False (BELOW minimum)
        """
        # CRITICAL: Must use <= for both comparisons
        # Using < would allow 5.20 to slip through when max is 5.10
        return config['buffer_min'] <= odds <= config['buffer_max']
    
    def check_filter(self, fixture):
        """
        Check if fixture passes the filter condition
        
        Args:
            fixture: Series or dict with fixture data
            
        Returns:
            tuple: (passed, in_buffer)
                passed: True if filter fully passed
                in_buffer: True if filter in buffer zone
        """
        if not self.has_filter:
            return True, False
        
        # Get filter column value
        filter_col = self.filter_condition['column']
        filter_value = fixture.get(filter_col)
        
        if pd.isna(filter_value) or filter_value is None:
            return False, False
        
        # Check filter condition
        operator = self.filter_condition['operator']
        threshold = self.filter_condition['value']
        
        if operator == '>':
            passed = filter_value > threshold
            in_buffer = filter_value > self.filter_buffer_min if self.filter_buffer_min else False
        elif operator == '>=':
            passed = filter_value >= threshold
            in_buffer = filter_value >= self.filter_buffer_min if self.filter_buffer_min else False
        elif operator == '<':
            passed = filter_value < threshold
            in_buffer = filter_value < self.filter_buffer_min if self.filter_buffer_min else False
        elif operator == '<=':
            passed = filter_value <= threshold
            in_buffer = filter_value <= self.filter_buffer_min if self.filter_buffer_min else False
        else:
            return False, False
        
        return passed, in_buffer
    
    def check_criteria(self, fixture):
        """
        Check if fixture meets all criteria for this system
        
        CRITICAL: This method enforces buffer range validation
        
        Args:
            fixture: Series or dict with fixture data
            
        Returns:
            tuple: (qualifies, config, reason)
                qualifies: Boolean if bet qualifies
                config: Configuration dict if qualifies
                reason: String explaining why/why not
        """
        league = fixture.get('League') or fixture.get('Competition')
        
        # Get configuration for this league
        config = self.get_config_for_league(league)
        if config is None:
            return False, None, f"No configuration for league: {league}"
        
        # Get odds
        odds = fixture.get(self.market_column)
        if pd.isna(odds) or odds is None:
            return False, None, f"Missing odds for {self.market_column}"
        
        # CRITICAL VALIDATION: Check if in buffer (exact range or buffer zone)
        # This is the main protection against invalid bets
        if not self.is_in_buffer(odds, config):
            # This rejection is CRITICAL - it prevents bets outside buffer range
            return False, None, f"Odds {odds:.2f} outside buffer {config['buffer_min']:.2f}-{config['buffer_max']:.2f}"
        
        # Check filter if applicable
        filter_passed, filter_in_buffer = self.check_filter(fixture)
        
        # For O2.5 Back, exclude if home odds < filter buffer minimum
        if self.system_name == 'O2.5 Back' and not filter_passed and not filter_in_buffer:
            return False, None, f"Filter failed: Home odds below minimum"
        
        # Bet qualifies!
        in_exact = self.is_in_exact_range(odds, config)
        
        if in_exact and filter_passed:
            reason = "In exact range, filter passed"
        elif in_exact and filter_in_buffer:
            reason = "In exact range, filter in buffer"
        elif filter_passed:
            reason = "In buffer zone, filter passed"
        else:
            reason = "In buffer zone, filter in buffer"
        
        return True, config, reason
    
    def generate_bet_signal(self, fixture):
        """
        Generate a bet signal for a fixture
        
        Args:
            fixture: Series or dict with fixture data
            
        Returns:
            dict: Bet signal with all relevant information, or None if doesn't qualify
        """
        qualifies, config, reason = self.check_criteria(fixture)
        
        if not qualifies:
            return None
        
        odds = fixture.get(self.market_column)
        league = fixture.get('League') or fixture.get('Competition')
        
        # Build bet signal
        signal = {
            'system': self.system_name,
            'league': league,
            'home_team': fixture.get('Home Team'),
            'away_team': fixture.get('Away Team'),
            'date': fixture.get('Date'),
            'time': fixture.get('Time'),
            'odds': odds,
            'odds_range': f"{config['exact_min']:.2f}-{config['exact_max']:.2f}",
            'buffer_range': f"{config['buffer_min']:.2f}-{config['buffer_max']:.2f}",
            'in_exact_range': self.is_in_exact_range(odds, config),
            'reason': reason
        }
        
        # Add filter status for O2.5 Back
        if self.system_name == 'O2.5 Back':
            filter_passed, filter_in_buffer = self.check_filter(fixture)
            signal['filter_passed'] = filter_passed
            signal['filter_in_buffer'] = filter_in_buffer
            signal['home_odds'] = fixture.get('Home Back Odds')
        
        return signal
    
    def scan_fixtures(self, fixtures_df):
        """
        Scan all fixtures and return qualifying bets
        
        This method applies strict validation - any bet returned has:
        1. Passed buffer range check (buffer_min <= odds <= buffer_max)
        2. Passed filter check (if applicable)
        3. Valid league configuration
        
        Args:
            fixtures_df: DataFrame with fixture data
            
        Returns:
            list: List of bet signals for qualifying fixtures
        """
        signals = []
        
        for _, fixture in fixtures_df.iterrows():
            signal = self.generate_bet_signal(fixture)
            if signal is not None:
                signals.append(signal)
        
        return signals
    
    def get_system_info(self):
        """
        Get information about this system
        
        Returns:
            dict: System information
        """
        return {
            'name': self.system_name,
            'description': f'{self.system_name} betting system',
            'market_column': self.market_column,
            'has_filter': self.has_filter
        }
