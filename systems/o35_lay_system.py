"""
O3.5 Lay Betting System

Lays over 3.5 goals when odds are in configured ranges.
"""

import pandas as pd


class O35LaySystem:
    """Over 3.5 Lay system - betting against over 3.5 goals"""
    
    def __init__(self, config):
        """Initialize O3.5 Lay system"""
        self.config = config
        self.system_name = "O3.5 Lay"
        self.default_buffer = 0.25
    
    def scan_fixtures(self, fixtures_df):
        """Scan fixtures for O3.5 Lay opportunities"""
        signals = []
        fixtures = fixtures_df.copy()
        
        # Identify columns
        if 'Competition' in fixtures.columns:
            league_col = 'Competition'
        elif 'League' in fixtures.columns:
            league_col = 'League'
        else:
            return signals
        
        # Find O3.5 Lay odds
        o35_col = None
        for col in ['O3.5 Lay Odds', 'O3.5', 'Over 3.5 Lay']:
            if col in fixtures.columns:
                o35_col = col
                break
        
        if not o35_col:
            return signals
        
        # Process fixtures
        for idx, row in fixtures.iterrows():
            league = row[league_col]
            
            if league not in self.config:
                continue
            
            league_config = self.config[league]
            
            try:
                o35_odds = float(row[o35_col])
            except (ValueError, TypeError):
                continue
            
            # Get odds ranges
            exact_min = league_config['odds_min']
            exact_max = league_config['odds_max']
            buffer = league_config.get('buffer', self.default_buffer)
            buffer_min = exact_min - buffer
            buffer_max = exact_max + buffer
            
            # Check if in range
            in_exact_range = exact_min <= o35_odds <= exact_max
            in_buffer_range = buffer_min <= o35_odds <= buffer_max
            
            if in_exact_range or in_buffer_range:
                signal = {
                    'system': self.system_name,
                    'league': league,
                    'home_team': row.get('Home Team', row.get('Home', '')),
                    'away_team': row.get('Away Team', row.get('Away', '')),
                    'odds': o35_odds,
                    'odds_range': f"{exact_min:.2f} - {exact_max:.2f}",
                    'in_exact_range': in_exact_range,
                    'filter_passed': True,
                    'date': row.get('Date', ''),
                    'time': row.get('Time', '')
                }
                
                signals.append(signal)
        
        return signals


def get_o35_lay_config(portfolio_stats):
    """Build O3.5 Lay configuration from portfolio stats"""
    config = {}
    
    for key, stats in portfolio_stats.items():
        if stats.get('system') == 'O3.5 Lay':
            league = stats.get('league')
            config[league] = {
                'odds_min': stats.get('Odds_Min', 0),
                'odds_max': stats.get('Odds_Max', 999),
                'buffer': 0.25
            }
    
    return config
