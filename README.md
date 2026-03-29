# Football Betting Model Application

## Overview

A comprehensive football betting model system that implements 5 proven betting systems across 45 league configurations with custom buffer zones and true value scoring.

## Systems Implemented

1. **Home Win** - 7 configurations (9-54% ROI)
2. **O2.5 Back** - 11 configurations (11-35% ROI) 
3. **O3.5 Lay** - 11 configurations (13-56% ROI)
4. **U1.5 Lay** - 8 configurations (15-49% ROI)
5. **FHGU0.5 Lay** - 8 configurations (26-57% ROI)

## Features

- **True Value Scoring**: Combines system ROI (40%), sample reliability (30%), and range compliance (30%)
- **Custom Buffer Zones**: Each configuration has tailored acceptable odds ranges
- **Automated Filtering**: O2.5 Back system requires Home odds > 2.00
- **Backtesting Engine**: Test strategies on 5+ years of historical data
- **Streamlit Dashboard**: Interactive web interface for daily bet selection
- **Modular Architecture**: Easy to add new systems and configurations

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone or download the project
cd football_betting_model

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Prepare Your Data

**Historical Data** (`data/historical_matches.csv`):
Required columns:
- Date
- League (Competition)
- Home Team
- Away Team
- Season
- Home Back Odds
- O2.5 Back Odds
- O3.5 Lay Odds
- U1.5 Lay Odds
- FHGU0.5 Lay Odds
- FTR (Full Time Result: H/D/A)
- FTHG (Full Time Home Goals)
- FTAG (Full Time Away Goals)

**Daily Fixtures** (`data/daily_fixtures.csv`):
Same format but without results (FTR, FTHG, FTAG)

### 2. Run Backtests

```python
from models.backtest import BacktestEngine

engine = BacktestEngine('data/historical_matches.csv')
results = engine.run_all_systems()
engine.print_summary(results)
```

### 3. Generate Daily Bets

```python
from models.daily_selector import DailyBetSelector

selector = DailyBetSelector('data/historical_matches.csv')
bets = selector.generate_selections('data/daily_fixtures.csv', '2026-03-13')
selector.export_to_excel(bets, 'daily_shortlist.xlsx')
```

### 4. Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Then open http://localhost:8501 in your browser.

## Project Structure

```
football_betting_model/
├── README.md
├── requirements.txt
├── config/
│   ├── systems_config.json      # All system configurations
│   └── buffer_zones.json         # Custom buffer zones
├── data/
│   ├── historical_matches.csv
│   └── daily_fixtures.csv
├── systems/
│   ├── __init__.py
│   ├── base_system.py           # Base class for all systems
│   ├── home_win.py
│   ├── o25_back.py
│   ├── o35_lay.py
│   ├── u15_lay.py
│   └── fhgu05_lay.py
├── models/
│   ├── __init__.py
│   ├── value_calculator.py      # True value scoring
│   ├── backtest.py              # Backtesting engine
│   └── daily_selector.py        # Daily bet selection
├── dashboard/
│   ├── app.py                   # Streamlit main app
│   ├── pages/
│   │   ├── daily_bets.py
│   │   ├── backtest_results.py
│   │   └── system_config.py
│   └── components/
│       ├── bet_display.py
│       └── charts.py
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   └── filters.py
└── tests/
    ├── test_systems.py
    └── test_value_calc.py
```

## Usage Examples

### Example 1: Check Today's Bets

```python
from models.daily_selector import DailyBetSelector
import pandas as pd

# Initialize
selector = DailyBetSelector('data/historical_matches.csv')

# Generate today's bets
bets = selector.generate_selections('data/daily_fixtures.csv', '2026-03-13')

# Filter HIGH confidence only
high_bets = bets[bets['Confidence'] == 'HIGH']
print(f"Found {len(high_bets)} HIGH confidence bets")

# Export to Excel
selector.export_to_excel(bets, 'todays_bets.xlsx')
```

### Example 2: Backtest Specific System

```python
from models.backtest import BacktestEngine

engine = BacktestEngine('data/historical_matches.csv')

# Backtest only O3.5 Lay system
results = engine.backtest_system('O3.5 Lay', 'Irish Premier League')

print(f"Total Bets: {results['total_bets']}")
print(f"ROI: {results['roi']:.2f}%")
print(f"Profit: {results['profit']:.2f} units")
```

### Example 3: Add New System

Create `systems/new_system.py`:

```python
from systems.base_system import BaseSystem

class NewSystem(BaseSystem):
    def __init__(self):
        super().__init__(
            name='New System',
            market_column='New Market Odds',
            has_filter=False
        )
    
    def check_criteria(self, fixture, config):
        # Your custom logic here
        return True  # or False
```

Add configuration to `config/systems_config.json`.

## Data Format Examples

### Historical Matches CSV

```csv
Date,League,Home Team,Away Team,Season,Home Back Odds,O2.5 Back Odds,O3.5 Lay Odds,FTR,FTHG,FTAG
2024-03-15,Irish Premier League,Shamrock Rovers,Derry,2024,2.05,1.85,5.50,H,3,1
2024-03-15,English Championship,Leeds,Ipswich,2023-2024,1.95,1.75,4.20,D,2,2
```

### Daily Fixtures CSV

```csv
Date,Time,League,Home Team,Away Team,Home Back Odds,O2.5 Back Odds,O3.5 Lay Odds
2026-03-13,19:45,Irish Premier League,Shelbourne,Shamrock Rovers,2.78,1.92,5.30
2026-03-13,20:00,English Championship,Birmingham,QPR,1.72,1.68,4.00
```

## Dashboard Features

### Daily Bets Page
- Upload today's fixtures
- View all qualifying bets sorted by value score
- Filter by confidence level (HIGH/SPECULATIVE)
- Filter by system
- Export to Excel

### Backtest Results Page
- View historical performance by system
- Filter by league, date range
- Interactive charts (ROI over time, bet distribution)
- Detailed statistics table

### System Configuration Page
- View all 45 configurations
- See buffer zones and ROI
- Edit configurations (advanced)

## Value Scoring Explained

**Formula**: `(ROI Score × 0.4) + (Sample Score × 0.3) + (Range Score × 0.3)`

- **ROI Score**: System's historical ROI normalized (0-40 points)
- **Sample Score**: Log-scaled sample size reliability (0-30 points)
- **Range Score**: 30 if in exact range, 15 if in buffer, 0 if outside

**Final Score**: Scaled to 0-20

**Interpretation**:
- 15-20: Excellent value (HIGH confidence)
- 10-14: Good value (SPECULATIVE)
- 5-9: Moderate value (monitor)
- 0-4: Low value (skip)

## Updating Data

### Weekly Historical Update

```python
from utils.data_loader import DataLoader

loader = DataLoader()

# Add new results
new_data = pd.read_csv('weekly_results.csv')
loader.append_to_historical(new_data, 'data/historical_matches.csv')
```

### Daily Fixtures

Simply replace `data/daily_fixtures.csv` with your new file or upload via dashboard.

## Troubleshooting

**Issue**: "No bets found"
- Check date format (YYYY-MM-DD)
- Verify fixture file has correct column names
- Ensure odds columns are numeric

**Issue**: "System not found"
- Check `config/systems_config.json`
- Verify system name matches exactly

**Issue**: "Value scores seem wrong"
- Rebuild historical stats: `python models/backtest.py --rebuild`
- Check buffer zones in `config/buffer_zones.json`

## Contributing

To add a new betting system:

1. Create system file in `systems/`
2. Add configuration to `config/systems_config.json`
3. Add buffer zones to `config/buffer_zones.json`
4. Run backtest to validate
5. Update dashboard to include new system

## Support

For issues or questions, check:
- This README
- Code comments in each module
- Example usage in `tests/` directory

## License

Private use only. All systems and configurations are proprietary.

## Version History

- v1.0 (March 2026): Initial release with 5 systems, 45 configurations
- Custom buffer zones implemented
- True value scoring system
- Streamlit dashboard

---

**Built with**: Python, Pandas, NumPy, Streamlit, Plotly
