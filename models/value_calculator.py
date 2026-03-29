"""
True Value Scoring Calculator

This module implements the value scoring system that combines:
- System Quality (ROI): 40% weight
- Sample Reliability: 30% weight  
- Range Compliance: 30% weight

Final score is scaled to 0-20 where:
- 15-20 = HIGH confidence (in exact range)
- 10-14 = SPECULATIVE (in buffer zone)
- 0-9 = Low value (skip)
"""

import numpy as np
import json
from pathlib import Path


class ValueCalculator:
    """Calculate value scores for betting opportunities"""
    
    def __init__(self, config_dir='config'):
        """
        Initialize the value calculator
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.portfolio_stats = self._load_portfolio_stats()
        self.max_roi = self.portfolio_stats['max_roi']
        
    def _load_portfolio_stats(self):
        """Load historical performance statistics"""
        stats_file = self.config_dir / 'portfolio_stats.json'
        with open(stats_file, 'r') as f:
            return json.load(f)
    
    def calculate_value_score(self, system, league, odds, config, home_odds=None):
        """
        Calculate the true value score for a bet
        
        Args:
            system: System name (e.g., 'O2.5 Back')
            league: League name
            odds: Current market odds
            config: Configuration dict with exact_min, exact_max, buffer_min, buffer_max
            home_odds: Home odds (required for O2.5 Back filter)
            
        Returns:
            dict with:
                - score: Final value score (0-20)
                - confidence: 'HIGH' or 'SPECULATIVE'
                - in_exact_range: Boolean
                - filter_passed: Boolean (if applicable)
                - breakdown: Dict with component scores
        """
        
        # Get historical stats
        key = f"{system}|{league}"
        if key not in self.portfolio_stats['stats']:
            return {
                'score': 0,
                'confidence': 'NO_DATA',
                'in_exact_range': False,
                'filter_passed': False,
                'breakdown': {}
            }
        
        stats = self.portfolio_stats['stats'][key]
        system_roi = stats['roi']
        sample_size = stats['total_bets']
        
        # COMPONENT 1: System Quality (40 points max)
        # Normalize ROI against portfolio maximum
        roi_score = (system_roi / self.max_roi) * 40
        
        # COMPONENT 2: Sample Reliability (30 points max)
        # Log scale, maxes out at 200 bets
        if sample_size > 0:
            sample_factor = min(np.log10(sample_size) / np.log10(200), 1.0)
            sample_score = sample_factor * 30
        else:
            sample_score = 0
        
        # COMPONENT 3: Range Compliance (30 points max)
        exact_min = config['exact_min']
        exact_max = config['exact_max']
        buffer_min = config['buffer_min']
        buffer_max = config['buffer_max']
        
        in_exact_range = (odds >= exact_min and odds <= exact_max)
        in_buffer = (odds >= buffer_min and odds <= buffer_max)
        
        # Exclude bets outside buffer completely
        if not in_buffer:
            return {
                'score': 0,
                'confidence': 'OUT_OF_RANGE',
                'in_exact_range': False,
                'filter_passed': False,
                'breakdown': {
                    'reason': f'Odds {odds:.2f} outside buffer {buffer_min:.2f}-{buffer_max:.2f}'
                }
            }
        
        # Score range compliance
        if in_exact_range:
            range_score = 30
            confidence = 'HIGH'
        else:
            range_score = 15
            confidence = 'SPECULATIVE'
        
        # Check filter if applicable (O2.5 Back only)
        filter_passed = True
        filter_in_buffer = False
        
        if system == 'O2.5 Back':
            if home_odds is None:
                return {
                    'score': 0,
                    'confidence': 'MISSING_FILTER',
                    'in_exact_range': False,
                    'filter_passed': False,
                    'breakdown': {'reason': 'Home odds required for O2.5 Back'}
                }
            
            # Exclude if Home < 1.80 (below filter buffer)
            if home_odds < 1.80:
                return {
                    'score': 0,
                    'confidence': 'FILTER_FAILED',
                    'in_exact_range': False,
                    'filter_passed': False,
                    'breakdown': {'reason': f'Home odds {home_odds:.2f} < 1.80'}
                }
            
            # Check filter compliance
            if home_odds >= 2.00:
                filter_passed = True
            else:  # 1.80 <= home_odds < 2.00 (in filter buffer)
                filter_passed = False
                filter_in_buffer = True
        
        # Apply filter buffer penalty if needed
        if system == 'O2.5 Back' and filter_in_buffer and confidence == 'SPECULATIVE':
            range_score = range_score * 0.7  # 30% penalty
        
        # Calculate total score (out of 100)
        total_score = roi_score + sample_score + range_score
        
        # Scale to 20
        final_score = (total_score / 100) * 20
        
        # Determine final confidence
        if not filter_passed and system == 'O2.5 Back':
            confidence = 'SPECULATIVE'
        
        return {
            'score': round(final_score, 1),
            'confidence': confidence,
            'in_exact_range': in_exact_range,
            'filter_passed': filter_passed,
            'breakdown': {
                'roi_score': round(roi_score, 2),
                'sample_score': round(sample_score, 2),
                'range_score': round(range_score, 2),
                'total_score': round(total_score, 2),
                'roi_pct': round(system_roi, 2),
                'sample_size': sample_size,
                'in_exact': in_exact_range,
                'in_buffer': in_buffer,
                'filter_status': 'passed' if filter_passed else 'buffer' if filter_in_buffer else 'N/A'
            }
        }
    
    def get_interpretation(self, score):
        """
        Get human-readable interpretation of a value score
        
        Args:
            score: Value score (0-20)
            
        Returns:
            str: Interpretation
        """
        if score >= 18:
            return "Exceptional value - odds near perfect center"
        elif score >= 15:
            return "Excellent value - strong bet"
        elif score >= 12:
            return "Good value - solid opportunity"
        elif score >= 10:
            return "Moderate value - speculative"
        elif score >= 5:
            return "Weak value - monitor only"
        else:
            return "Low value - skip"
    
    def batch_calculate(self, fixtures_df, system, config):
        """
        Calculate scores for multiple fixtures at once
        
        Args:
            fixtures_df: DataFrame with fixtures
            system: System name
            config: Configuration dict
            
        Returns:
            DataFrame with added value_score column
        """
        scores = []
        
        for _, fixture in fixtures_df.iterrows():
            # Get odds based on system
            if system == 'Home Win':
                odds = fixture.get('Home Back Odds')
            elif system == 'O2.5 Back':
                odds = fixture.get('O2.5 Back Odds')
            elif system == 'O3.5 Lay':
                odds = fixture.get('O3.5 Lay Odds')
            elif system == 'U1.5 Lay':
                odds = fixture.get('U1.5 Lay Odds')
            elif system == 'FHGU0.5 Lay':
                odds = fixture.get('FHGU0.5 Lay Odds')
            else:
                scores.append(0)
                continue
            
            home_odds = fixture.get('Home Back Odds') if system == 'O2.5 Back' else None
            league = config['league']
            
            result = self.calculate_value_score(system, league, odds, config, home_odds)
            scores.append(result['score'])
        
        fixtures_df = fixtures_df.copy()
        fixtures_df['value_score'] = scores
        
        return fixtures_df


# Example usage
if __name__ == "__main__":
    # Initialize calculator
    calc = ValueCalculator()
    
    # Example: Calculate score for O2.5 Back Scottish Premiership
    config = {
        'league': 'Scottish Premiership',
        'exact_min': 1.80,
        'exact_max': 2.10,
        'buffer_min': 1.70,
        'buffer_max': 2.40
    }
    
    result = calc.calculate_value_score(
        system='O2.5 Back',
        league='Scottish Premiership',
        odds=2.00,
        config=config,
        home_odds=4.40
    )
    
    print(f"Value Score: {result['score']}/20")
    print(f"Confidence: {result['confidence']}")
    print(f"Interpretation: {calc.get_interpretation(result['score'])}")
    print(f"\nBreakdown:")
    for key, value in result['breakdown'].items():
        print(f"  {key}: {value}")
