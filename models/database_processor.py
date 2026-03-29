"""
Database Processor

Recalculates all system statistics from historical match data.
Updates portfolio_stats.json with fresh data.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


class DatabaseProcessor:
    """Process historical database and update system statistics"""
    
    def __init__(self, config_dir='config'):
        self.config_dir = Path(config_dir)
        self.load_systems_config()
    
    def load_systems_config(self):
        """Load system configurations"""
        with open(self.config_dir / 'systems_config.json', 'r') as f:
            self.systems = json.load(f)
    
    def load_historical_data(self, filepath):
        """Load historical match database"""
        print(f"Loading historical data from {filepath}...")
        
        # Load with header row 2 (like FTS Advanced format)
        df = pd.read_excel(filepath, header=1, engine='openpyxl')
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Standardize league column
        if 'Competition' in df.columns:
            df['League'] = df['Competition']
        
        # Ensure Date column is datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Remove rows with invalid dates
        df = df[df['Date'].notna()]
        
        print(f"✅ Loaded {len(df):,} matches")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"   Leagues: {df['League'].nunique()}")
        
        return df
    
    def calculate_system_stats(self, historical_df, system_name, config):
        """Calculate statistics for a single system configuration"""
        
        market_col = self.systems[system_name]['market_column']
        has_filter = self.systems[system_name]['has_filter']
        
        league = config['league']
        exact_min = config['exact_min']
        exact_max = config['exact_max']
        
        # Filter for this league
        league_df = historical_df[historical_df['League'] == league].copy()
        
        if len(league_df) == 0:
            return None
        
        # Check if market column exists
        if market_col not in league_df.columns:
            return None
        
        # Filter by odds range (exact range only for backtesting)
        in_range = (league_df[market_col] >= exact_min) & (league_df[market_col] <= exact_max)
        bets_df = league_df[in_range].copy()
        
        # Apply filter if needed (O2.5 Back)
        if has_filter and system_name == 'O2.5 Back':
            if 'Home Back Odds' in bets_df.columns:
                bets_df = bets_df[bets_df['Home Back Odds'] >= 2.00]
        
        if len(bets_df) == 0:
            return None
        
        # Calculate results based on system type
        if system_name == 'Home Win':
            # Back bets - win if FTR == 'H'
            bets_df['Win'] = (bets_df['FTR'] == 'H').astype(int)
            bets_df['Profit'] = bets_df.apply(
                lambda row: (row[market_col] - 1) if row['Win'] else -1,
                axis=1
            )
        
        elif system_name == 'O2.5 Back':
            # Back over 2.5 - win if total goals > 2.5
            bets_df['Total_Goals'] = bets_df['FTHG'] + bets_df['FTAG']
            bets_df['Win'] = (bets_df['Total_Goals'] > 2.5).astype(int)
            bets_df['Profit'] = bets_df.apply(
                lambda row: (row[market_col] - 1) if row['Win'] else -1,
                axis=1
            )
        
        elif system_name == 'O3.5 Lay':
            # Lay over 3.5 - win if total goals <= 3.5
            bets_df['Total_Goals'] = bets_df['FTHG'] + bets_df['FTAG']
            bets_df['Win'] = (bets_df['Total_Goals'] <= 3.5).astype(int)
            bets_df['Profit'] = bets_df.apply(
                lambda row: 1 if row['Win'] else -(row[market_col] - 1),
                axis=1
            )
        
        elif system_name == 'U1.5 Lay':
            # Lay under 1.5 - win if total goals >= 2
            bets_df['Total_Goals'] = bets_df['FTHG'] + bets_df['FTAG']
            bets_df['Win'] = (bets_df['Total_Goals'] >= 2).astype(int)
            bets_df['Profit'] = bets_df.apply(
                lambda row: 1 if row['Win'] else -(row[market_col] - 1),
                axis=1
            )
        
        elif system_name == 'FHGU0.5 Lay':
            # Lay first half under 0.5 - need first half goals columns
            if 'HTHG' in bets_df.columns and 'HTAG' in bets_df.columns:
                bets_df['HT_Goals'] = bets_df['HTHG'] + bets_df['HTAG']
                bets_df['Win'] = (bets_df['HT_Goals'] >= 1).astype(int)
                bets_df['Profit'] = bets_df.apply(
                    lambda row: 1 if row['Win'] else -(row[market_col] - 1),
                    axis=1
                )
            else:
                # No half-time data available
                return None
        
        # Calculate statistics
        total_bets = len(bets_df)
        total_profit = bets_df['Profit'].sum()
        total_wins = bets_df['Win'].sum()
        strike_rate = (total_wins / total_bets) * 100 if total_bets > 0 else 0
        roi = (total_profit / total_bets) * 100 if total_bets > 0 else 0
        
        # Calculate season breakdown
        if 'Season' in bets_df.columns:
            season_results = []
            for season in sorted(bets_df['Season'].unique()):
                season_df = bets_df[bets_df['Season'] == season]
                season_bets = len(season_df)
                season_profit = season_df['Profit'].sum()
                season_wins = season_df['Win'].sum()
                season_sr = (season_wins / season_bets) * 100 if season_bets > 0 else 0
                season_roi = (season_profit / season_bets) * 100 if season_bets > 0 else 0
                
                season_results.append({
                    'Season': str(season),
                    'Bets': int(season_bets),
                    'PL': round(season_profit, 2),
                    'SR': round(season_sr, 2),
                    'ROI': round(season_roi, 2)
                })
        else:
            season_results = []
        
        return {
            'system': system_name,
            'league': league,
            'roi': round(roi, 2),
            'total_bets': int(total_bets),
            'strike_rate': round(strike_rate, 2),
            'profit': round(total_profit, 2),
            'season_results': season_results
        }
    
    def process_all_systems(self, historical_df):
        """Process all systems and configurations"""
        
        print("\n" + "="*80)
        print("PROCESSING ALL SYSTEMS")
        print("="*80)
        print()
        
        portfolio_stats = {}
        max_roi = 0
        
        for system_name, system_config in self.systems.items():
            print(f"\nProcessing {system_name}...")
            
            for config in system_config['configurations']:
                league = config['league']
                print(f"  - {league}...", end=" ")
                
                stats = self.calculate_system_stats(historical_df, system_name, config)
                
                if stats:
                    key = f"{system_name}|{league}"
                    portfolio_stats[key] = stats
                    
                    if stats['roi'] > max_roi:
                        max_roi = stats['roi']
                    
                    print(f"✅ {stats['total_bets']} bets, {stats['roi']:.2f}% ROI")
                else:
                    print("❌ No data")
        
        print()
        print("="*80)
        print(f"COMPLETE: Processed {len(portfolio_stats)} configurations")
        print(f"Max ROI: {max_roi:.2f}%")
        print("="*80)
        
        return {
            'max_roi': max_roi,
            'stats': portfolio_stats
        }
    
    def save_stats(self, stats, output_file='config/portfolio_stats.json'):
        """Save updated statistics"""
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✅ Statistics saved to {output_file}")
    
    def update_from_database(self, database_file):
        """Complete workflow: load data, calculate stats, save"""
        
        print("="*80)
        print("DATABASE UPDATE WORKFLOW")
        print("="*80)
        print()
        
        # Load data
        historical_df = self.load_historical_data(database_file)
        
        # Process all systems
        stats = self.process_all_systems(historical_df)
        
        # Save updated stats
        self.save_stats(stats)
        
        print("\n✅ Database update complete!")
        
        return stats


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_processor.py path/to/historical_data.xlsx")
        sys.exit(1)
    
    processor = DatabaseProcessor()
    stats = processor.update_from_database(sys.argv[1])
    
    print("\nSummary:")
    print(f"  Total configurations: {len(stats['stats'])}")
    print(f"  Max ROI: {stats['max_roi']:.2f}%")
    print(f"  Total bets: {sum(s['total_bets'] for s in stats['stats'].values()):,}")
