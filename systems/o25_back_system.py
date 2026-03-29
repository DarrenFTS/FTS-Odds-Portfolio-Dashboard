"""
O2.5 Back Betting System

Backs over 2.5 goals when odds are in configured ranges and home odds filter passes.
"""

import pandas as pd


class O25BackSystem:
    """
    Over 2.5 goals backing system
    
    Backs over 2.5 goals when:
    - O2.5 odds within configured range for the league
    - Home odds >= 2.00 (filter)
    """
    
    def __init__(self, config):
        """Initialize O2.5 Back system"""
        self.config = config
        self.system_name = "O2.5 Back"
        self.default_buffer = 0.20
        self.home_odds_filter = 2.00  # Home must be >= 2.00
    
    def scan_fixtures(self, fixtures_df):
        """Scan fixtures for O2.5 Back opportunities"""
        signals = []
        fixtures = fixtures_df.copy()
        
        # Identify columns
        if 'Competition' in fixtures.columns:
            league_col = 'Competition'
        elif 'League' in fixtures.columns:
            league_col = 'League'
        else:
            return signals
        
        # Find O2.5 Back odds
        o25_col = None
        for col in ['O2.5 Back Odds', 'O2.5', 'Over 2.5']:
            if col in fixtures.columns:
                o25_col = col
                break
        
        if not o25_col:
            return signals
        
        # Find Home odds for filter
        home_odds_col = None
        for col in ['Home Back Odds', 'Home', '1']:
            if col in fixtures.columns:
                home_odds_col = col
                break
        
        # Process fixtures
        for idx, row in fixtures.iterrows():
            league = row[league_col]
            
            if league not in self.config:
                continue
            
            league_config = self.config[league]
            
            try:
                o25_odds = float(row[o25_col])
            except (ValueError, TypeError):
                continue
            
            # Get home odds for filter
            home_odds = None
            if home_odds_col:
                try:
                    home_odds = float(row[home_odds_col])
                except (ValueError, TypeError):
                    pass
            
            # Check filter
            filter_passed = True
            filter_in_buffer = False
            
            if home_odds is not None:
                if home_odds >= self.home_odds_filter:
                    filter_passed = True
                elif home_odds >= 1.80:  # Buffer zone
                    filter_passed = False
                    filter_in_buffer = True
                else:
                    continue  # Too low, skip
            
            # Get odds ranges
            exact_min = league_config['odds_min']
            exact_max = league_config['odds_max']
            buffer = league_config.get('buffer', self.default_buffer)
            buffer_min = exact_min - buffer
            buffer_max = exact_max + buffer
            
            # Check if in range
            in_exact_range = exact_min <= o25_odds <= exact_max
            in_buffer_range = buffer_min <= o25_odds <= buffer_max
            
            if in_exact_range or in_buffer_range:
                signal = {
                    'system': self.system_name,
                    'league': league,
                    'home_team': row.get('Home Team', row.get('Home', '')),
                    'away_team': row.get('Away Team', row.get('Away', '')),
                    'odds': o25_odds,
                    'odds_range': f"{exact_min:.2f} - {exact_max:.2f}",
                    'in_exact_range': in_exact_range,
                    'filter_passed': filter_passed,
                    'filter_in_buffer': filter_in_buffer,
                    'date': row.get('Date', ''),
                    'time': row.get('Time', '')
                }
                
                signals.append(signal)
        
        return signals


def get_o25_back_config(portfolio_stats):
    """Build O2.5 Back configuration from portfolio stats"""
    config = {}
    
    for key, stats in portfolio_stats.items():
        if stats.get('system') == 'O2.5 Back':
            league = stats.get('league')
            config[league] = {
                'odds_min': stats.get('Odds_Min', 0),
                'odds_max': stats.get('Odds_Max', 999),
                'buffer': 0.20
            }
    
    return config
