# Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Installation

```bash
cd football_betting_model
pip install -r requirements.txt
```

### Step 2: Verify Setup

```bash
python -c "from models.daily_selector import DailyBetSelector; print('✅ Setup successful!')"
```

### Step 3: Generate Today's Bets

**Option A: Command Line (Quickest)**

```bash
python run_daily.py path/to/your/fixtures.csv 2026-03-13
```

**Option B: Web Dashboard (Best Experience)**

```bash
streamlit run dashboard/app.py
```

Then:
1. Upload your fixtures file
2. Select date
3. Click "Generate Selections"
4. Export to Excel

**Option C: Python Script (Most Flexible)**

```python
from models.daily_selector import DailyBetSelector

selector = DailyBetSelector()
bets = selector.generate_selections('fixtures.csv', '2026-03-13')
selector.export_to_excel(bets, 'my_bets.xlsx')
selector.print_summary(bets)
```

---

## 📁 Required Data Format

Your fixtures file needs these columns:

### Must Have:
- `Date` - Match date
- `Time` - Kick-off time
- `League` or `Competition` - League name
- `Home Team` - Home team name
- `Away Team` - Away team name

### Odds Columns (include those you want to bet on):
- `Home Back Odds` - Home win odds (needed for all bets, especially O2.5 Back filter)
- `O2.5 Back Odds` - Over 2.5 goals odds
- `O3.5 Lay Odds` - Over 3.5 goals lay odds
- `U1.5 Lay Odds` - Under 1.5 goals lay odds
- `FHGU0.5 Lay Odds` - First half under 0.5 goals lay odds

### Example CSV:

```csv
Date,Time,League,Home Team,Away Team,Home Back Odds,O2.5 Back Odds,O3.5 Lay Odds,U1.5 Lay Odds,FHGU0.5 Lay Odds
2026-03-13,19:45,Irish Premier League,Shelbourne,Shamrock Rovers,2.78,1.92,5.30,5.50,5.40
2026-03-13,20:00,English Championship,Birmingham,QPR,1.72,1.68,4.00,4.50,4.20
```

---

## 📊 Understanding the Output

### Value Score (0-20)
- **18-20**: Exceptional value
- **15-18**: Excellent value (HIGH confidence)
- **12-15**: Good value  
- **10-12**: Moderate value (SPECULATIVE)
- **Below 10**: Low value (usually not shown)

### Confidence Levels
- **🟢 HIGH**: Odds in exact range + filter passed (if applicable)
- **🔴 SPECULATIVE**: Odds in buffer zone OR filter in buffer

### What the Scoring Means

**Formula**: `(ROI × 40%) + (Sample Size × 30%) + (Range × 30%)`

Example: O3.5 Lay Irish Premier (17.0/20)
- System ROI: 46.3% → ROI Component: 32.4/40
- Sample: 53 bets → Sample Component: 24.6/30
- In exact range → Range Component: 30/30
- **Total: (32.4 + 24.6 + 30) / 100 × 20 = 17.0/20** ✅

---

## 🎯 Daily Workflow

### Morning Routine (5 minutes):

1. **Get Fixtures**
   - Download from Betfair, Oddschecker, or your data provider
   - Save as CSV or Excel

2. **Generate Bets**
   ```bash
   python run_daily.py fixtures.csv
   ```
   Or open dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

3. **Review Output**
   - Focus on HIGH confidence bets (15-20/20)
   - Check SPECULATIVE (10-14/20) for value
   - Read filter status for O2.5 Back

4. **Place Bets**
   - Prioritize high value scores
   - Note the exact range for each bet
   - Monitor odds movement

### Evening (Optional):
- Track results
- Update P/L in Excel
- Review what worked

---

## 🔧 Common Issues

### "No qualifying bets found"
✓ Check your fixtures file has the correct date
✓ Verify column names match expected format
✓ Ensure odds columns are numeric (not text)

### "Config file not found"
✓ Run from project root directory: `cd football_betting_model`
✓ Check `config/` folder exists with JSON files

### "Module not found"
✓ Install requirements: `pip install -r requirements.txt`
✓ Python 3.8+ required

---

## 💡 Pro Tips

### Maximizing Value
1. **Focus on HIGH confidence** (15-20/20)
2. **Top system: FHGU0.5 Lay** (26-57% ROI)
3. **Strong: O3.5 Lay** (13-56% ROI)
4. **O2.5 Back**: Always check Home odds filter

### System-Specific Tips

**O2.5 Back**:
- Needs Home > 2.00 for HIGH
- 1.80-1.99 = buffer (SPECULATIVE)
- Below 1.80 = excluded

**FHGU0.5 Lay**:
- Highest ROI system (up to 57%)
- Smaller sample sizes in some leagues
- Trust the value score

**O3.5 Lay**:
- Very reliable (600+ bets in some leagues)
- Irish Premier League star performer

### Bankroll Management
- **Conservative**: Only HIGH (15-20/20)
- **Balanced**: HIGH + top SPECULATIVE (13-14/20)
- **Aggressive**: All above 10/20

Recommended: Start conservative, track results, adjust

---

## 📖 Next Steps

### Learn More
- Read full `README.md` for architecture details
- Check `models/value_calculator.py` for scoring logic
- Explore `systems/` to understand each betting system

### Customize
- Edit `config/buffer_zones.json` to adjust ranges
- Modify `models/value_calculator.py` for different weights
- Add new systems in `systems/` folder

### Track Performance
- Use Excel P/L columns
- Calculate actual ROI vs expected
- Refine based on results

---

## ✅ You're Ready!

You now have a complete betting model that:
- ✅ Implements 5 proven systems
- ✅ Uses true value scoring
- ✅ Enforces custom buffer zones
- ✅ Filters automatically (O2.5 Back)
- ✅ Generates daily shortlists
- ✅ Exports to Excel
- ✅ Has web dashboard

**Run your first shortlist:**
```bash
python run_daily.py your_fixtures.csv
```

Good luck! 🍀⚽📊
