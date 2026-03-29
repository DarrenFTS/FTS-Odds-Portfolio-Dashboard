"""
Advanced Value Scoring System

Calculates a comprehensive 0-100 value score for each bet based on:
- Expected Value (model probability vs market odds)
- Historical ROI (system, league, odds band)
- Sample size reliability
- Odds band performance
- League-specific performance

Author: Sports Betting Data Science Team
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy import stats


class ValueScorer:
    """
    Advanced value scoring system for betting opportunities
    
    Combines multiple factors into a 0-100 score:
    - Expected Value (30 points)
    - Historical ROI (25 points)
    - Sample Reliability (20 points)
    - League Performance (15 points)
    - Odds Band Performance (10 points)
    """
    
    def __init__(self, config_dir='config', historical_data_path=None):
        """
        Initialize the value scorer
        
        Args:
            config_dir: Path to configuration files
            historical_data_path: Path to historical match data (for calculating probabilities)
        """
        self.config_dir = Path(config_dir)
        self.historical_data_path = historical_data_path
        
        # Load portfolio statistics
        self.load_portfolio_stats()
        
        # Load or calculate strike rates
        self.load_strike_rates()
    
    def load_portfolio_stats(self):
        """Load historical performance statistics"""
        with open(self.config_dir / 'portfolio_stats.json', 'r') as f:
            data = json.load(f)
            self.portfolio_stats = data['stats']
            self.max_roi = data['max_roi']
    
    def load_strike_rates(self):
        """
        Load or calculate historical strike rates for each system/league
        These are used to estimate model probability
        """
        self.strike_rates = {}
        
        for key, stats in self.portfolio_stats.items():
            system, league = key.split('|')
            strike_rate = stats['strike_rate'] / 100  # Convert to decimal
            
            self.strike_rates[key] = {
                'strike_rate': strike_rate,
                'sample_size': stats['total_bets']
            }
    
    def calculate_model_probability(self, system, league, odds):
        """
        Calculate model's implied probability based on historical strike rate
        
        Args:
            system: System name
            league: League name
            odds: Bet odds
            
        Returns:
            float: Model probability (0-1)
        """
        key = f"{system}|{league}"
        
        if key not in self.strike_rates:
            return None
        
        strike_rate = self.strike_rates[key]['strike_rate']
        
        # For back bets: model probability = strike rate
        if system in ['Home Win', 'O2.5 Back']:
            model_prob = strike_rate
        
        # For lay bets: model probability = 1 - strike rate (probability it loses)
        elif system in ['O3.5 Lay', 'U1.5 Lay', 'FHGU0.5 Lay']:
            model_prob = 1 - strike_rate  # Prob that bet wins (over doesn't happen)
        
        else:
            model_prob = strike_rate
        
        return model_prob
    
    def calculate_market_probability(self, odds, bet_type='back'):
        """
        Calculate market's implied probability from odds
        
        Args:
            odds: Decimal odds
            bet_type: 'back' or 'lay'
            
        Returns:
            float: Market probability (0-1)
        """
        if bet_type == 'back':
            # Back bet: market prob = 1 / odds
            market_prob = 1 / odds
        else:
            # Lay bet: we're betting against, so prob = 1 - (1/odds)
            market_prob = 1 - (1 / odds)
        
        return market_prob
    
    def calculate_expected_value(self, model_prob, market_prob, odds, bet_type='back'):
        """
        Calculate expected value of the bet
        
        EV = (model_prob × (odds - 1)) - (1 - model_prob) × 1
        
        Args:
            model_prob: Model's probability estimate
            market_prob: Market's implied probability
            odds: Decimal odds
            bet_type: 'back' or 'lay'
            
        Returns:
            float: Expected value as percentage
        """
        if model_prob is None:
            return 0
        
        if bet_type == 'back':
            # EV for back bet
            win_amount = odds - 1
            lose_amount = -1
            ev = (model_prob * win_amount) + ((1 - model_prob) * lose_amount)
        else:
            # EV for lay bet
            win_amount = 1
            lose_amount = -(odds - 1)
            ev = (model_prob * win_amount) + ((1 - model_prob) * lose_amount)
        
        # Convert to percentage
        ev_pct = ev * 100
        
        return ev_pct
    
    def get_odds_band(self, odds):
        """
        Categorize odds into bands for performance analysis
        
        Args:
            odds: Decimal odds
            
        Returns:
            str: Odds band category
        """
        if odds < 1.5:
            return "1.0-1.5"
        elif odds < 2.0:
            return "1.5-2.0"
        elif odds < 2.5:
            return "2.0-2.5"
        elif odds < 3.0:
            return "2.5-3.0"
        elif odds < 4.0:
            return "3.0-4.0"
        elif odds < 5.0:
            return "4.0-5.0"
        elif odds < 6.0:
            return "5.0-6.0"
        else:
            return "6.0+"
    
    def calculate_odds_band_performance(self, system, league, odds_band):
        """
        Get historical ROI for bets in the same odds band
        
        This requires historical data - for now returns system average
        Can be enhanced with actual odds band data
        
        Args:
            system: System name
            league: League name
            odds_band: Odds band (e.g., "2.0-2.5")
            
        Returns:
            float: Historical ROI for this odds band
        """
        key = f"{system}|{league}"
        
        if key in self.portfolio_stats:
            # For now, return system ROI
            # TODO: Calculate actual odds band ROI from historical data
            return self.portfolio_stats[key]['roi']
        
        return 0
    
    def calculate_sample_reliability(self, sample_size):
        """
        Calculate reliability score based on sample size
        
        Uses logarithmic scale with diminishing returns
        
        Args:
            sample_size: Number of historical bets
            
        Returns:
            float: Reliability score (0-1)
        """
        if sample_size <= 0:
            return 0
        
        # Logarithmic scale: maxes out at 200 bets
        # 10 bets = ~0.33, 50 bets = ~0.71, 100 bets = ~0.86, 200+ bets = 1.0
        reliability = min(np.log10(sample_size) / np.log10(200), 1.0)
        
        return reliability
    
    def calculate_value_score(self, system, league, odds, in_exact_range=True, filter_passed=True):
        """
        Calculate comprehensive 0-100 value score
        
        Components:
        - Expected Value (30 points): Model edge over market
        - Historical ROI (25 points): System's historical performance
        - Sample Reliability (20 points): Confidence based on sample size
        - League Performance (15 points): League-specific ROI
        - Odds Band Performance (10 points): Performance in this odds range
        
        Args:
            system: System name
            league: League name
            odds: Bet odds
            in_exact_range: Boolean if bet is in exact range (vs buffer)
            filter_passed: Boolean if filter passed (for O2.5 Back)
            
        Returns:
            dict with score and components
        """
        key = f"{system}|{league}"
        
        # Check if we have data for this system
        if key not in self.portfolio_stats:
            return {
                'value_score': 0,
                'components': {},
                'error': f'No historical data for {system} - {league}'
            }
        
        stats = self.portfolio_stats[key]
        
        # Determine bet type
        bet_type = 'lay' if 'Lay' in system else 'back'
        
        # === COMPONENT 1: EXPECTED VALUE (30 points) ===
        model_prob = self.calculate_model_probability(system, league, odds)
        market_prob = self.calculate_market_probability(odds, bet_type)
        ev_pct = self.calculate_expected_value(model_prob, market_prob, odds, bet_type)
        
        # Scale EV to 30 points
        # EV of 50% = max points, 0% = 15 points, negative = reduced points
        if ev_pct >= 50:
            ev_points = 30
        elif ev_pct >= 0:
            ev_points = 15 + (ev_pct / 50) * 15  # 0% EV = 15 pts, 50% = 30 pts
        else:
            # Negative EV reduces points
            ev_points = max(0, 15 + (ev_pct / 50) * 15)
        
        # === COMPONENT 2: HISTORICAL ROI (25 points) ===
        system_roi = stats['roi']
        
        # Normalize ROI against maximum (57.15%)
        roi_normalized = min(system_roi / self.max_roi, 1.0)
        roi_points = roi_normalized * 25
        
        # === COMPONENT 3: SAMPLE RELIABILITY (20 points) ===
        sample_size = stats['total_bets']
        reliability = self.calculate_sample_reliability(sample_size)
        sample_points = reliability * 20
        
        # === COMPONENT 4: LEAGUE PERFORMANCE (15 points) ===
        # Same as system ROI for now (since we're already filtering by league)
        league_roi = system_roi
        league_normalized = min(league_roi / self.max_roi, 1.0)
        league_points = league_normalized * 15
        
        # === COMPONENT 5: ODDS BAND PERFORMANCE (10 points) ===
        odds_band = self.get_odds_band(odds)
        odds_band_roi = self.calculate_odds_band_performance(system, league, odds_band)
        odds_band_normalized = min(max(odds_band_roi, 0) / self.max_roi, 1.0)
        odds_band_points = odds_band_normalized * 10
        
        # === RANGE AND FILTER ADJUSTMENTS ===
        # Penalty if in buffer zone (not exact range)
        if not in_exact_range:
            range_penalty = 0.85  # 15% penalty
        else:
            range_penalty = 1.0
        
        # Additional penalty for O2.5 Back if filter not fully passed
        if system == 'O2.5 Back' and not filter_passed:
            filter_penalty = 0.90  # Additional 10% penalty
        else:
            filter_penalty = 1.0
        
        # Calculate total score
        total_points = (ev_points + roi_points + sample_points + 
                       league_points + odds_band_points)
        
        # Apply penalties
        final_score = total_points * range_penalty * filter_penalty
        
        # Cap at 100
        final_score = min(final_score, 100)
        
        return {
            'value_score': round(final_score, 1),
            'model_probability': round(model_prob * 100, 2) if model_prob else None,
            'market_probability': round(market_prob * 100, 2),
            'expected_value': round(ev_pct, 2),
            'historical_roi': round(system_roi, 2),
            'league_roi': round(league_roi, 2),
            'sample_size': sample_size,
            'odds_band': odds_band,
            'odds_band_roi': round(odds_band_roi, 2),
            'components': {
                'ev_points': round(ev_points, 1),
                'roi_points': round(roi_points, 1),
                'sample_points': round(sample_points, 1),
                'league_points': round(league_points, 1),
                'odds_band_points': round(odds_band_points, 1),
                'range_penalty': range_penalty,
                'filter_penalty': filter_penalty
            },
            'interpretation': self.interpret_score(final_score)
        }
    
    def interpret_score(self, score):
        """
        Provide interpretation of value score
        
        Args:
            score: Value score (0-100)
            
        Returns:
            str: Human-readable interpretation
        """
        if score >= 80:
            return "Exceptional - Strong edge, high confidence"
        elif score >= 70:
            return "Excellent - Very strong bet"
        elif score >= 60:
            return "Very Good - Clear value"
        elif score >= 50:
            return "Good - Solid opportunity"
        elif score >= 40:
            return "Fair - Moderate value"
        elif score >= 30:
            return "Marginal - Low confidence"
        else:
            return "Weak - Consider avoiding"
    
    def rank_daily_bets(self, bets_df):
        """
        Score and rank all bets for the day
        
        Args:
            bets_df: DataFrame with daily bets from daily_selector
            
        Returns:
            DataFrame with added scoring columns, sorted by value_score
        """
        scored_bets = []
        
        for _, bet in bets_df.iterrows():
            # Calculate value score
            score_result = self.calculate_value_score(
                system=bet['System'],
                league=bet['League'],
                odds=bet['Odds'],
                in_exact_range=bet.get('In Exact Range', True),
                filter_passed=bet.get('Filter Passed', True)
            )
            
            # Add all score components to bet
            bet_dict = bet.to_dict()
            bet_dict.update({
                'Value Score': score_result['value_score'],
                'Model Probability': score_result['model_probability'],
                'Market Probability': score_result['market_probability'],
                'Expected Value %': score_result['expected_value'],
                'Historical ROI %': score_result['historical_roi'],
                'League ROI %': score_result['league_roi'],
                'Sample Size': score_result['sample_size'],
                'Odds Band': score_result['odds_band'],
                'Odds Band ROI %': score_result['odds_band_roi'],
                'Interpretation': score_result['interpretation']
            })
            
            scored_bets.append(bet_dict)
        
        # Convert to DataFrame
        scored_df = pd.DataFrame(scored_bets)
        
        # Sort by value score (descending)
        scored_df = scored_df.sort_values('Value Score', ascending=False)
        
        return scored_df
    
    def get_top_value_bets(self, scored_df, top_n=10, min_score=50):
        """
        Get top value bets above a minimum score threshold
        
        Args:
            scored_df: DataFrame with scored bets
            top_n: Number of top bets to return
            min_score: Minimum value score threshold
            
        Returns:
            DataFrame with top value bets
        """
        # Filter by minimum score
        filtered = scored_df[scored_df['Value Score'] >= min_score]
        
        # Return top N
        return filtered.head(top_n)
    
    def analyze_sample_sizes(self):
        """
        Analyze all systems for sample size adequacy
        
        Returns:
            DataFrame with sample size analysis
        """
        analysis = []
        
        for key, stats in self.portfolio_stats.items():
            system, league = key.split('|')
            sample_size = stats['total_bets']
            
            reliability = self.calculate_sample_reliability(sample_size)
            
            # Categorize sample adequacy
            if sample_size >= 100:
                adequacy = "Excellent"
                confidence = "High"
            elif sample_size >= 50:
                adequacy = "Good"
                confidence = "Moderate-High"
            elif sample_size >= 30:
                adequacy = "Fair"
                confidence = "Moderate"
            elif sample_size >= 20:
                adequacy = "Marginal"
                confidence = "Low-Moderate"
            else:
                adequacy = "Poor"
                confidence = "Low"
            
            analysis.append({
                'System': system,
                'League': league,
                'Sample Size': sample_size,
                'Reliability Score': round(reliability, 3),
                'Adequacy': adequacy,
                'Confidence Level': confidence,
                'ROI': stats['roi'],
                'Strike Rate': stats['strike_rate']
            })
        
        analysis_df = pd.DataFrame(analysis)
        analysis_df = analysis_df.sort_values('Sample Size', ascending=False)
        
        return analysis_df


# Example usage and testing
if __name__ == "__main__":
    # Initialize scorer
    scorer = ValueScorer()
    
    # Example bet
    print("="*80)
    print("EXAMPLE VALUE SCORE CALCULATION")
    print("="*80)
    print()
    
    result = scorer.calculate_value_score(
        system='O3.5 Lay',
        league='Irish Premier League',
        odds=5.30,
        in_exact_range=True,
        filter_passed=True
    )
    
    print(f"Bet: O3.5 Lay - Irish Premier League @ 5.30")
    print()
    print(f"VALUE SCORE: {result['value_score']}/100")
    print(f"Interpretation: {result['interpretation']}")
    print()
    print(f"Expected Value: {result['expected_value']}%")
    print(f"Model Probability: {result['model_probability']}%")
    print(f"Market Probability: {result['market_probability']}%")
    print()
    print(f"Historical ROI: {result['historical_roi']}%")
    print(f"Sample Size: {result['sample_size']} bets")
    print(f"Odds Band: {result['odds_band']} (ROI: {result['odds_band_roi']}%)")
    print()
    print("Component Breakdown:")
    for component, value in result['components'].items():
        print(f"  {component}: {value}")
    
    print("\n" + "="*80)
    print("SAMPLE SIZE ANALYSIS")
    print("="*80)
    print()
    
    sample_analysis = scorer.analyze_sample_sizes()
    
    print("Systems with Low Sample Sizes (< 30 bets):")
    low_sample = sample_analysis[sample_analysis['Sample Size'] < 30]
    print(low_sample.to_string(index=False))
    
    print("\n⚠️  WARNING: Systems with < 30 bets have low statistical confidence")
    print(f"   Total systems with low samples: {len(low_sample)}")
