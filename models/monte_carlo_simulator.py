"""
Monte Carlo Simulator for Betting Systems

Runs 1,000+ simulations to analyze:
- True expected ROI with confidence intervals
- Maximum drawdown risk
- Profit distribution
- Probability of profit/loss
- Risk of ruin
- Bankroll requirements

Based on your actual historical performance data.
"""

import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path


class MonteCarloSimulator:
    """Monte Carlo simulation for betting systems"""
    
    def __init__(self, config_dir='config'):
        self.config_dir = Path(config_dir)
        self.load_portfolio_stats()
    
    def load_portfolio_stats(self):
        """Load historical performance data"""
        with open(self.config_dir / 'portfolio_stats.json', 'r') as f:
            data = json.load(f)
            self.portfolio_stats = data['stats']
            self.max_roi = data['max_roi']
    
    def simulate_system(self, system_name, league, num_simulations=1000, num_bets=100):
        """
        Run Monte Carlo simulation for a specific system configuration
        
        Args:
            system_name: Name of the system (e.g., 'O2.5 Back')
            league: League name
            num_simulations: Number of Monte Carlo runs (default: 1000)
            num_bets: Number of bets per simulation (default: 100)
            
        Returns:
            dict with simulation results
        """
        # Get historical stats
        key = f"{system_name}|{league}"
        if key not in self.portfolio_stats:
            raise ValueError(f"No data found for {system_name} - {league}")
        
        stats = self.portfolio_stats[key]
        historical_roi = stats['roi']
        historical_sr = stats['strike_rate'] / 100  # Convert to decimal
        sample_size = stats['total_bets']
        
        print(f"\nSimulating: {system_name} - {league}")
        print(f"Historical: {sample_size} bets, {historical_roi:.2f}% ROI, {historical_sr*100:.2f}% SR")
        print(f"Running {num_simulations:,} simulations of {num_bets} bets each...")
        
        # Storage for results
        all_final_pls = []
        all_max_drawdowns = []
        all_rois = []
        all_cumulative_paths = []
        
        # Run simulations
        for sim in range(num_simulations):
            cumulative_pl = 0
            max_pl = 0
            max_drawdown = 0
            pl_path = [0]  # Track cumulative P/L path
            
            for bet in range(num_bets):
                # Simulate bet outcome based on historical strike rate
                win = np.random.random() < historical_sr
                
                # Estimate average odds from ROI and SR
                # ROI = (SR * (avg_odds - 1)) - (1 - SR)
                # Solving for avg_odds: avg_odds = (ROI/100 + 1) / SR
                if historical_sr > 0:
                    estimated_avg_odds = (historical_roi/100 + 1) / historical_sr
                else:
                    estimated_avg_odds = 2.0  # Fallback
                
                # Calculate P/L for this bet
                if win:
                    pl = estimated_avg_odds - 1
                else:
                    pl = -1
                
                cumulative_pl += pl
                pl_path.append(cumulative_pl)
                
                # Track peak
                if cumulative_pl > max_pl:
                    max_pl = cumulative_pl
                
                # Calculate drawdown from peak
                drawdown = max_pl - cumulative_pl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Store results
            final_roi = (cumulative_pl / num_bets) * 100
            all_final_pls.append(cumulative_pl)
            all_max_drawdowns.append(max_drawdown)
            all_rois.append(final_roi)
            all_cumulative_paths.append(pl_path)
        
        # Calculate statistics
        results = {
            'system': system_name,
            'league': league,
            'num_simulations': num_simulations,
            'num_bets': num_bets,
            'historical_roi': historical_roi,
            'historical_sr': historical_sr * 100,
            'historical_sample': sample_size,
            
            # ROI statistics
            'mean_roi': np.mean(all_rois),
            'median_roi': np.median(all_rois),
            'roi_std': np.std(all_rois),
            'roi_5th_percentile': np.percentile(all_rois, 5),
            'roi_95th_percentile': np.percentile(all_rois, 95),
            
            # Profit statistics
            'mean_profit': np.mean(all_final_pls),
            'median_profit': np.median(all_final_pls),
            'profit_std': np.std(all_final_pls),
            'min_profit': np.min(all_final_pls),
            'max_profit': np.max(all_final_pls),
            
            # Drawdown statistics
            'mean_drawdown': np.mean(all_max_drawdowns),
            'median_drawdown': np.median(all_max_drawdowns),
            'max_drawdown': np.max(all_max_drawdowns),
            'drawdown_95th_percentile': np.percentile(all_max_drawdowns, 95),
            
            # Probability of profit
            'prob_profit': (np.array(all_final_pls) > 0).sum() / num_simulations * 100,
            'prob_loss': (np.array(all_final_pls) < 0).sum() / num_simulations * 100,
            
            # Raw data for plotting
            'all_rois': all_rois,
            'all_profits': all_final_pls,
            'all_drawdowns': all_max_drawdowns,
            'sample_paths': all_cumulative_paths[:100]  # Store first 100 paths for plotting
        }
        
        return results
    
    def simulate_portfolio(self, num_simulations=1000, num_bets_per_system=20):
        """
        Simulate entire portfolio (all 45 configurations)
        
        Args:
            num_simulations: Number of Monte Carlo runs
            num_bets_per_system: Bets per system per simulation
            
        Returns:
            dict with portfolio-level results
        """
        print("\n" + "="*80)
        print("PORTFOLIO MONTE CARLO SIMULATION")
        print("="*80)
        print(f"\nSimulations: {num_simulations:,}")
        print(f"Bets per system: {num_bets_per_system}")
        print()
        
        # Run simulation for each configuration
        all_configs_results = []
        
        for key, stats in self.portfolio_stats.items():
            system, league = key.split('|')
            
            try:
                result = self.simulate_system(
                    system, 
                    league, 
                    num_simulations=num_simulations,
                    num_bets=num_bets_per_system
                )
                all_configs_results.append(result)
            except Exception as e:
                print(f"  ⚠️  Error simulating {system} - {league}: {str(e)}")
        
        # Aggregate portfolio results
        portfolio_results = {
            'num_configs': len(all_configs_results),
            'num_simulations': num_simulations,
            'total_bets_per_sim': num_bets_per_system * len(all_configs_results),
            'configs': all_configs_results
        }
        
        # Calculate portfolio-level statistics
        portfolio_rois = []
        portfolio_profits = []
        portfolio_drawdowns = []
        
        for sim in range(num_simulations):
            sim_total_profit = sum(c['all_profits'][sim] for c in all_configs_results)
            sim_total_bets = num_bets_per_system * len(all_configs_results)
            sim_roi = (sim_total_profit / sim_total_bets) * 100
            sim_max_dd = max(c['all_drawdowns'][sim] for c in all_configs_results)
            
            portfolio_rois.append(sim_roi)
            portfolio_profits.append(sim_total_profit)
            portfolio_drawdowns.append(sim_max_dd)
        
        portfolio_results['portfolio_mean_roi'] = np.mean(portfolio_rois)
        portfolio_results['portfolio_median_roi'] = np.median(portfolio_rois)
        portfolio_results['portfolio_roi_std'] = np.std(portfolio_rois)
        portfolio_results['portfolio_roi_5th'] = np.percentile(portfolio_rois, 5)
        portfolio_results['portfolio_roi_95th'] = np.percentile(portfolio_rois, 95)
        portfolio_results['portfolio_mean_profit'] = np.mean(portfolio_profits)
        portfolio_results['portfolio_max_drawdown'] = np.max(portfolio_drawdowns)
        portfolio_results['portfolio_prob_profit'] = (np.array(portfolio_profits) > 0).sum() / num_simulations * 100
        
        portfolio_results['all_portfolio_rois'] = portfolio_rois
        portfolio_results['all_portfolio_profits'] = portfolio_profits
        
        print("\n" + "="*80)
        print("PORTFOLIO SIMULATION COMPLETE")
        print("="*80)
        
        return portfolio_results
    
    def print_summary(self, results):
        """Print simulation summary"""
        print("\n" + "="*80)
        print(f"MONTE CARLO RESULTS: {results['system']} - {results['league']}")
        print("="*80)
        print()
        print(f"Historical Performance:")
        print(f"  Sample Size: {results['historical_sample']} bets")
        print(f"  ROI: {results['historical_roi']:.2f}%")
        print(f"  Strike Rate: {results['historical_sr']:.2f}%")
        print()
        print(f"Simulation Setup:")
        print(f"  Simulations: {results['num_simulations']:,}")
        print(f"  Bets per simulation: {results['num_bets']}")
        print()
        print(f"Expected ROI (with {results['num_bets']} bets):")
        print(f"  Mean: {results['mean_roi']:.2f}%")
        print(f"  Median: {results['median_roi']:.2f}%")
        print(f"  Std Dev: {results['roi_std']:.2f}%")
        print(f"  90% Confidence Interval: {results['roi_5th_percentile']:.2f}% to {results['roi_95th_percentile']:.2f}%")
        print()
        print(f"Expected Profit (units):")
        print(f"  Mean: {results['mean_profit']:.2f}")
        print(f"  Range: {results['min_profit']:.2f} to {results['max_profit']:.2f}")
        print()
        print(f"Risk Analysis:")
        print(f"  Mean Max Drawdown: {results['mean_drawdown']:.2f} units")
        print(f"  95th Percentile Drawdown: {results['drawdown_95th_percentile']:.2f} units")
        print(f"  Worst Case Drawdown: {results['max_drawdown']:.2f} units")
        print()
        print(f"Probability of Outcomes:")
        print(f"  Profit: {results['prob_profit']:.1f}%")
        print(f"  Loss: {results['prob_loss']:.1f}%")
        print()
    
    def create_visualizations(self, results):
        """Create comprehensive visualization dashboard"""
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'ROI Distribution',
                'Profit Distribution',
                'Drawdown Distribution',
                'Cumulative P/L Paths (100 samples)',
                'ROI Confidence Intervals',
                'Profit vs Drawdown'
            ),
            specs=[
                [{"type": "histogram"}, {"type": "histogram"}],
                [{"type": "histogram"}, {"type": "scatter"}],
                [{"type": "box"}, {"type": "scatter"}]
            ]
        )
        
        # 1. ROI Distribution
        fig.add_trace(
            go.Histogram(
                x=results['all_rois'],
                name='ROI Distribution',
                marker_color='#366092',
                nbinsx=50
            ),
            row=1, col=1
        )
        fig.add_vline(
            x=results['historical_roi'],
            line_dash="dash",
            line_color="red",
            annotation_text="Historical",
            row=1, col=1
        )
        
        # 2. Profit Distribution
        fig.add_trace(
            go.Histogram(
                x=results['all_profits'],
                name='Profit Distribution',
                marker_color='#2ecc71',
                nbinsx=50
            ),
            row=1, col=2
        )
        fig.add_vline(x=0, line_dash="dash", line_color="red", row=1, col=2)
        
        # 3. Drawdown Distribution
        fig.add_trace(
            go.Histogram(
                x=results['all_drawdowns'],
                name='Max Drawdown',
                marker_color='#e74c3c',
                nbinsx=50
            ),
            row=2, col=1
        )
        
        # 4. Sample Paths
        for path in results['sample_paths']:
            fig.add_trace(
                go.Scatter(
                    y=path,
                    mode='lines',
                    line=dict(width=0.5, color='rgba(54, 96, 146, 0.1)'),
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 5. ROI Box Plot with Confidence Intervals
        fig.add_trace(
            go.Box(
                y=results['all_rois'],
                name='ROI Range',
                marker_color='#366092',
                boxmean='sd'
            ),
            row=3, col=1
        )
        
        # 6. Profit vs Drawdown Scatter
        fig.add_trace(
            go.Scatter(
                x=results['all_drawdowns'],
                y=results['all_profits'],
                mode='markers',
                marker=dict(
                    size=3,
                    color=results['all_rois'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="ROI %")
                ),
                name='Simulations'
            ),
            row=3, col=2
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red", row=3, col=2)
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text=f"Monte Carlo Analysis: {results['system']} - {results['league']}<br>" +
                       f"<sub>{results['num_simulations']:,} simulations × {results['num_bets']} bets | " +
                       f"Historical: {results['historical_roi']:.2f}% ROI from {results['historical_sample']} bets</sub>",
            showlegend=False
        )
        
        # Update axes
        fig.update_xaxes(title_text="ROI (%)", row=1, col=1)
        fig.update_xaxes(title_text="Profit (units)", row=1, col=2)
        fig.update_xaxes(title_text="Max Drawdown (units)", row=2, col=1)
        fig.update_xaxes(title_text="Bet Number", row=2, col=2)
        fig.update_xaxes(title_text="Max Drawdown (units)", row=3, col=2)
        
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative P/L", row=2, col=2)
        fig.update_yaxes(title_text="ROI (%)", row=3, col=1)
        fig.update_yaxes(title_text="Profit (units)", row=3, col=2)
        
        return fig
    
    def calculate_bankroll_requirements(self, results, confidence_level=0.95):
        """
        Calculate recommended bankroll based on drawdown risk
        
        Args:
            results: Simulation results
            confidence_level: Confidence level (default: 95%)
            
        Returns:
            dict with bankroll recommendations
        """
        # Get drawdown at confidence level
        percentile = confidence_level * 100
        required_bankroll = np.percentile(results['all_drawdowns'], percentile)
        
        # Add safety margin
        conservative_bankroll = required_bankroll * 1.5
        
        return {
            'confidence_level': confidence_level,
            f'drawdown_{int(percentile)}th_percentile': required_bankroll,
            'recommended_bankroll': conservative_bankroll,
            'unit_size_1pct': conservative_bankroll / 100,
            'interpretation': f"With {int(confidence_level*100)}% confidence, you won't exceed {required_bankroll:.1f} units drawdown"
        }


# Example usage
if __name__ == "__main__":
    simulator = MonteCarloSimulator()
    
    # Simulate a specific system
    results = simulator.simulate_system(
        system_name='O3.5 Lay',
        league='Irish Premier League',
        num_simulations=1000,
        num_bets=100
    )
    
    # Print summary
    simulator.print_summary(results)
    
    # Calculate bankroll requirements
    bankroll = simulator.calculate_bankroll_requirements(results)
    print(f"\nBankroll Recommendations:")
    print(f"  95% Confidence Drawdown: {bankroll['drawdown_95th_percentile']:.1f} units")
    print(f"  Recommended Bankroll: {bankroll['recommended_bankroll']:.1f} units")
    print(f"  {bankroll['interpretation']}")
    
    # Create visualizations
    fig = simulator.create_visualizations(results)
    fig.write_html('monte_carlo_results.html')
    print("\n✅ Visualization saved to monte_carlo_results.html")
