"""
Home Win Betting System

Backs the home team to win when odds are in configured ranges.
"""

import pandas as pd


class HomeWinSystem:
    """
    Home Win betting system
    
    Backs home team victory when:
    - Home odds within configured range for the league
    - No additional filters
    """
    
    def __init__(self, config):
        """
        Initialize Home Win system
        
        Args:
            config: Dictionary with league configurations
                   Each config has: odds_min, odds_max, buffer (optional)
        """
        self.config = config
        self.system_name = "Home Win"
        
        # Default buffer if not specified (0.20 on each side)
        self.default_buffer = 0.20
    
    def scan_fixtures(self, fixtures_df):
        """
        Scan fixtures for Home Win opportunities
        
        Args:
            fixtures_df: DataFrame with columns:
                - League/Competition
                - Home Team
                - Away Team  
                - Home Back Odds (or similar)
                - Date
                - Time
        
        Returns:
            List of signals (dicts with bet details)
        """
        signals = []
        
        # Identify relevant columns
        fixtures = fixtures_df.copy()
        
        # League column
        if 'Competition' in fixtures.columns:
            league_col = 'Competition'
        elif 'League' in fixtures.columns:
            league_col = 'League'
        else:
            return signals  # No league column found
        
        # Home odds column
        home_odds_col = None
        for col in fixtures.columns:
            if 'Home' in str(col) and 'Back' in str(col) and 'Odds' in str(col):
                home_odds_col = col
                break
        
        if not home_odds_col:
            return signals  # No home odds found
        
        # Process each fixture
        for idx, row in fixtures.iterrows():
            league = row[league_col]
            
            # Check if we have config for this league
            if league not in self.config:
                continue
            
            league_config = self.config[league]
            
            try:
                home_odds = float(row[home_odds_col])
            except (ValueError, TypeError):
                continue  # Invalid odds
            
            # Get odds ranges
            exact_min = league_config['odds_min']
            exact_max = league_config['odds_max']
            
            # Buffer (default 0.20 unless specified)
            buffer = league_config.get('buffer', self.default_buffer)
            buffer_min = exact_min - buffer
            buffer_max = exact_max + buffer
            
            # Check if in range
            in_exact_range = exact_min <= home_odds <= exact_max
            in_buffer_range = buffer_min <= home_odds <= buffer_max
            
            if in_exact_range or in_buffer_range:
                # Create signal
                signal = {
                    'system': self.system_name,
                    'league': league,
                    'home_team': row.get('Home Team', row.get('Home', '')),
                    'away_team': row.get('Away Team', row.get('Away', '')),
                    'odds': home_odds,
                    'odds_range': f"{exact_min:.2f} - {exact_max:.2f}",
                    'in_exact_range': in_exact_range,
                    'date': row.get('Date', ''),
                    'time': row.get('Time', ''),
                    'filter_passed': True  # No filter for Home Win
                }
                
                signals.append(signal)
        
        return signals


def get_home_win_config(portfolio_stats):
    """
    Build Home Win configuration from portfolio stats
    
    Args:
        portfolio_stats: Dict of portfolio configurations
    
    Returns:
        Dict of league configs for Home Win
    """
    config = {}
    
    for key, stats in portfolio_stats.items():
        if stats.get('system') == 'Home Win':
            league = stats.get('league')
            config[league] = {
                'odds_min': stats.get('Odds_Min', 0),
                'odds_max': stats.get('Odds_Max', 999),
                'buffer': 0.20  # Standard buffer
            }
    
    return config
