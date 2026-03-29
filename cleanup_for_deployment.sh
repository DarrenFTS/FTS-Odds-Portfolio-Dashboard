#!/bin/bash
# Cleanup script for Streamlit Cloud deployment
# Run this to organize your project before pushing to GitHub

echo "========================================================================"
echo "CLEANING UP PROJECT FOR STREAMLIT CLOUD DEPLOYMENT"
echo "========================================================================"

cd "/Users/darrensummers/Desktop/FTSIncome/25-26/FTS/Claude/FTS Odds Python/football_betting_model"

# Create backup first
echo ""
echo "1. Creating backup..."
BACKUP_DIR="../football_betting_model_backup_$(date +%Y%m%d_%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

# Delete unnecessary Python files from root
echo ""
echo "2. Removing unnecessary Python files from root directory..."
rm -f check_actual_file.py
rm -f debug_portfolio_stats.py
rm -f debug_selector.py
rm -f diagnostic_check.py
rm -f examples.py
rm -f rebuild_portfolio_stats.py
rm -f run_daily.py
rm -f run_portfolio_analysis.py
rm -f test_selector_output.py
echo "✅ Removed debug/test files from root"

# Delete all Excel files (will be uploaded by users)
echo ""
echo "3. Removing Excel files (users will upload these)..."
rm -f *.xlsx
rm -f data/*.xlsx
echo "✅ Removed Excel files"

# Delete __pycache__ and .pyc files
echo ""
echo "4. Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "✅ Removed cache files"

# Delete .DS_Store files
echo ""
echo "5. Removing macOS system files..."
find . -name ".DS_Store" -delete 2>/dev/null
echo "✅ Removed .DS_Store files"

# Delete tests directory if it's empty or has only __init__.py
echo ""
echo "6. Checking tests directory..."
if [ -d "tests" ]; then
    if [ -z "$(ls -A tests | grep -v __pycache__ | grep -v .pyc)" ]; then
        rm -rf tests
        echo "✅ Removed empty tests directory"
    else
        echo "⚠️  Tests directory has files - keeping it"
    fi
fi

# Delete utils if only has __init__.py
echo ""
echo "7. Checking utils directory..."
if [ -d "utils" ]; then
    FILE_COUNT=$(ls -A utils | grep -v __pycache__ | grep -v .pyc | wc -l)
    if [ $FILE_COUNT -le 1 ]; then
        rm -rf utils
        echo "✅ Removed utils directory (only had __init__.py)"
    else
        echo "⚠️  Utils directory has files - keeping it"
    fi
fi

# Delete data directory if only has Excel files
echo ""
echo "8. Checking data directory..."
if [ -d "data" ]; then
    if [ -z "$(ls -A data | grep -v .xlsx | grep -v __pycache__)" ]; then
        rm -rf data
        echo "✅ Removed data directory (only had Excel files)"
    else
        echo "⚠️  Data directory has other files - keeping it"
    fi
fi

# Create .gitignore if missing
echo ""
echo "9. Creating/updating .gitignore..."
cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.pyc
venv/
env/
.Python
*.so

# Streamlit
.streamlit/secrets.toml

# Data files - users upload these
*.xlsx
*.csv
*.xls

# OS
.DS_Store
.AppleDouble
.LSOverride
._*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log

# Temporary files
*.tmp
*.temp
temp_*

# Backup files
*.backup
*.old
*.bak

# Distribution / packaging
dist/
build/
*.egg-info/

# Unit test / coverage
.coverage
htmlcov/
.pytest_cache/
EOL
echo "✅ Created .gitignore"

# Update requirements.txt
echo ""
echo "10. Updating requirements.txt..."
cat > requirements.txt << 'EOL'
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
plotly>=5.17.0
python-dateutil>=2.8.0
EOL
echo "✅ Updated requirements.txt"

# Show final structure
echo ""
echo "========================================================================"
echo "CLEANUP COMPLETE!"
echo "========================================================================"
echo ""
echo "Final structure:"
echo "----------------"
find . -type f \( -name "*.py" -o -name "*.json" -o -name "*.txt" -o -name "*.md" \) | \
    grep -v __pycache__ | \
    grep -v .pyc | \
    grep -v "$BACKUP_DIR" | \
    sort

echo ""
echo "========================================================================"
echo "FILES TO COMMIT TO GITHUB:"
echo "========================================================================"
echo "✅ dashboard/app.py"
echo "✅ dashboard/pages/ (if exists)"
echo "✅ models/enhanced_daily_selector.py"
echo "✅ models/value_calculator.py (if needed)"
echo "✅ systems/*.py (all 7 files)"
echo "✅ config/portfolio_stats.json"
echo "✅ requirements.txt"
echo "✅ .gitignore"
echo "✅ README.md"

echo ""
echo "❌ EXCLUDED (via .gitignore):"
echo "   - All *.xlsx files (users upload these)"
echo "   - __pycache__ folders"
echo "   - .DS_Store files"
echo "   - Debug/test scripts"

echo ""
echo "========================================================================"
echo "NEXT STEPS:"
echo "========================================================================"
echo "1. Review the changes above"
echo "2. Check your dashboard still works:"
echo "   streamlit run dashboard/app.py"
echo "3. If everything works, proceed to GitHub upload"
echo ""
echo "Backup saved at: $BACKUP_DIR"
echo "========================================================================"
