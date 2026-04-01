"""
Football Betting Model - Streamlit Dashboard

Main application for the web interface.

Usage:
    streamlit run dashboard/app.py

Features:
- Upload daily fixtures
- View qualifying bets
- Filter by confidence and system
- Export to Excel
- View system configurations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.enhanced_daily_selector import EnhancedDailySelector as DailyBetSelector
from models.value_calculator import ValueCalculator
from models.monte_carlo_simulator import MonteCarloSimulator

# Initialize portfolio stats in session state (for database updates)
if 'portfolio_stats' not in st.session_state:
    with open('config/portfolio_stats.json', 'r') as f:
        st.session_state.portfolio_stats = json.load(f)

# Function to get portfolio stats (from session state if updated, otherwise file)
def get_portfolio_stats():
    """Get portfolio stats from session state (updated) or file (default)"""
    if 'portfolio_stats' in st.session_state:
        return st.session_state.portfolio_stats
    else:
        with open('config/portfolio_stats.json', 'r') as f:
            return json.load(f)

# Page configuration
st.set_page_config(
    page_title="Football Betting Model",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #366092;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .high-confidence {
        background-color: #C6EFCE;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .speculative {
        background-color: #FFC7CE;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
st.session_state.selector = DailyBetSelector('config')

if 'selections' not in st.session_state:
    st.session_state.selections = None

if 'monte_carlo_results' not in st.session_state:
    st.session_state.monte_carlo_results = None

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/366092/FFFFFF?text=Football+Betting", use_container_width=True)
    st.markdown("### ⚽ Football Betting Model")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Daily Selections", "📈 Performance", "🎲 Monte Carlo", "📥 Database Upload", "⚙️ System Config"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    st.metric("Total Systems", "5")
    st.metric("Configurations", "45")
    st.metric("Max ROI", "57.15%")

# Main content area
if page == "📊 Daily Selections":
    st.markdown('<div class="main-header">📊 Daily Betting Selections</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload fixtures and generate today\'s bets</div>', unsafe_allow_html=True)
    
    # File upload
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Daily Fixtures (CSV or Excel)",
            type=['csv', 'xlsx'],
            help="Upload your daily fixtures file with odds data"
        )
    
    with col2:
        target_date = st.date_input(
            "Target Date",
            value=pd.Timestamp.now(),
            help="Filter fixtures by this date"
        )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        if uploaded_file.name.endswith('.csv'):
            temp_file = Path("temp_fixtures.csv")
        else:
            temp_file = Path("temp_fixtures.xlsx")
        
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Generate selections button
        if st.button("🔍 Generate Selections", type="primary"):
            with st.spinner("Scanning fixtures and calculating value scores..."):
                try:
                    selections = st.session_state.selector.generate_selections(
                        str(temp_file),
                        target_date
                    )
                    st.session_state.selections = selections
                    
                    if len(selections) > 0:
                        st.success(f"✅ Found {len(selections)} qualifying bets!")
                    else:
                        st.warning("No qualifying bets found for this date.")
                
                except Exception as e:
                    st.error(f"Error processing fixtures: {str(e)}")
    
    # Display selections if available
    if st.session_state.selections is not None and len(st.session_state.selections) > 0:
        selections = st.session_state.selections
        
        st.markdown("---")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Bets", len(selections))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            high_count = len(selections[selections['Value Score'] >= 60])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🟢 GOOD+ (50+)", high_count)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            exceptional_count = len(selections[selections['Value Score'] >= 70])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("⭐ EXCEPTIONAL (80+)", exceptional_count)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            avg_score = selections['Value Score'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Avg Score", f"{avg_score:.1f}/100")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Filters
        st.markdown("### 🔍 Filter Bets")
        col1, col2 = st.columns(2)
        
        with col1:
            # Get unique confidence levels from data
            unique_confidence = selections['Confidence'].unique().tolist()
            confidence_filter = st.multiselect(
                "Confidence Level",
                options=unique_confidence,
                default=unique_confidence
            )
        
        with col2:
            system_filter = st.multiselect(
                "System",
                options=selections['System'].unique().tolist(),
                default=selections['System'].unique().tolist()
            )
        
        # Apply filters
        filtered = selections[
            (selections['Confidence'].isin(confidence_filter)) &
            (selections['System'].isin(system_filter))
        ]
        
        st.markdown(f"### 📋 Showing {len(filtered)} Bets")
        
        # Display bets
        for idx, (_, bet) in enumerate(filtered.iterrows(), 1):
            # Determine color based on value score
            score = bet['Value Score']
            if score >= 70:
                conf_class = "high-confidence"
                conf_icon = "⭐"
            elif score >= 60:
                conf_class = "high-confidence"
                conf_icon = "🟢"
            elif score >= 50:
                conf_class = "speculative"
                conf_icon = "🟡"
            else:
                conf_class = "speculative"
                conf_icon = "🔴"
            
            with st.container():
                st.markdown(f'<div class="{conf_class}">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"**{idx}. {bet['Home Team']} vs {bet['Away Team']}**")
                    st.caption(f"{bet['League']} • {bet['Time']}")
                
                with col2:
                    st.markdown(f"**{bet['System']}**")
                    st.caption(f"Odds: {bet['Odds']:.2f} (Range: {bet['Odds Range']})")
                    if bet.get('Expected Value %'):
                        st.caption(f"EV: {bet['Expected Value %']:+.1f}%")
                    if bet.get('Filter Status'):
                        st.caption(bet['Filter Status'])
                
                with col3:
                    st.markdown(f"**{conf_icon} {bet['Value Score']:.1f}/100**")
                    st.caption(bet['Confidence'])
                    if bet.get('Interpretation'):
                        st.caption(f"_{bet['Interpretation']}_")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Export button
        st.markdown("---")
        if st.button("📥 Export to Excel"):
            output_file = f"daily_shortlist_{target_date.strftime('%Y%m%d')}.xlsx"
            st.session_state.selector.export_to_excel(filtered, output_file)
            st.success(f"✅ Exported to {output_file}")
            
            # Offer download
            with open(output_file, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=f,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif page == "📈 Performance":
    st.markdown('<div class="main-header">📈 Historical Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">System statistics and backtesting</div>', unsafe_allow_html=True)
    
    # Load stats using session state function
    portfolio = get_portfolio_stats()
    
    stats_data = []
    for key, stat in portfolio['stats'].items():
        stats_data.append(stat)
    
    stats_df = pd.DataFrame(stats_data)
    
    # Summary by system
    st.markdown("### Performance by System")
    
    summary = stats_df.groupby('system').agg({
        'roi': 'mean',
        'total_bets': 'sum',
        'profit': 'sum',
        'strike_rate': 'mean'
    }).round(2)
    
    summary = summary.rename(columns={
        'roi': 'Avg ROI (%)',
        'total_bets': 'Total Bets',
        'profit': 'Total Profit',
        'strike_rate': 'Avg SR (%)'
    })
    
    st.dataframe(summary, use_container_width=True)
    
    # Detailed table
    st.markdown("### All Configurations")
    
    display_df = stats_df[['system', 'league', 'roi', 'total_bets', 'strike_rate', 'profit']]
    display_df = display_df.rename(columns={
        'system': 'System',
        'league': 'League',
        'roi': 'ROI (%)',
        'total_bets': 'Bets',
        'strike_rate': 'SR (%)',
        'profit': 'Profit'
    })
    display_df = display_df.sort_values('ROI (%)', ascending=False)
    
    st.dataframe(display_df, use_container_width=True, height=600)

elif page == "⚙️ System Config":
    st.markdown('<div class="main-header">⚙️ System Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View and manage betting systems</div>', unsafe_allow_html=True)
    
    # Load configuration
    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    
    # Select system
    system_name = st.selectbox(
        "Select System",
        options=list(config.keys())
    )
    
    system_config = config[system_name]
    
    # Display system info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### System Details")
        st.write(f"**Market:** {system_config['market_column']}")
        st.write(f"**Has Filter:** {system_config['has_filter']}")
        if system_config['has_filter']:
            st.write(f"**Filter:** {system_config['filter_condition']}")
        st.write(f"**Configurations:** {len(system_config['configurations'])}")
    
    with col2:
        st.markdown("### Performance")
        # Load stats using session state function
        stats = get_portfolio_stats()
        
        system_stats = [
            v for k, v in stats['stats'].items() 
            if v['system'] == system_name
        ]
        
        if system_stats:
            avg_roi = sum(s['roi'] for s in system_stats) / len(system_stats)
            total_bets = sum(s['total_bets'] for s in system_stats)
            total_profit = sum(s['profit'] for s in system_stats)
            
            st.metric("Average ROI", f"{avg_roi:.2f}%")
            st.metric("Total Bets", total_bets)
            st.metric("Total Profit", f"{total_profit:.2f} units")
    
    # Show configurations table
    st.markdown("### League Configurations")
    
    config_df = pd.DataFrame(system_config['configurations'])
    config_df = config_df.rename(columns={
        'league': 'League',
        'exact_min': 'Exact Min',
        'exact_max': 'Exact Max',
        'buffer_min': 'Buffer Min',
        'buffer_max': 'Buffer Max'
    })
    
    st.dataframe(config_df, use_container_width=True)

elif page == "🎲 Monte Carlo":
    st.markdown('<div class="main-header">🎲 Monte Carlo Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Run 1,000+ simulations to analyze true ROI, drawdowns, and risk</div>', unsafe_allow_html=True)
    
    # Load portfolio stats using session state function
    portfolio_stats_mc = get_portfolio_stats()
    
    # Create tabs
    tab1, tab2 = st.tabs(["🎯 Single System", "📊 Full Portfolio"])
    
    with tab1:
        st.markdown("### Analyze Individual System")
        
        col1, col2 = st.columns(2)
        
        with col1:
            all_systems = ['Home Win', 'O2.5 Back', 'O3.5 Lay', 'U1.5 Lay', 'FHGU0.5 Lay']
            selected_system = st.selectbox("Select System", all_systems)
            
            system_leagues = [
                key.split('|')[1] 
                for key in portfolio_stats_mc['stats'].keys() 
                if key.startswith(selected_system)
            ]
            selected_league = st.selectbox("Select League", system_leagues)
        
        with col2:
            num_sims = st.selectbox(
                "Number of Simulations",
                [1000, 5000, 10000],
                index=0,
                help="More simulations = more accurate (but slower)"
            )
            
            num_bets = st.selectbox(
                "Bets per Simulation",
                [50, 100, 200, 500],
                index=1,
                help="How many bets to simulate"
            )
        
        if st.button("🎲 Run Monte Carlo Simulation", type="primary"):
            with st.spinner(f"Running {num_sims:,} simulations... This may take 30-60 seconds..."):
                try:
                    simulator = MonteCarloSimulator('config')
                    results = simulator.simulate_system(
                        system_name=selected_system,
                        league=selected_league,
                        num_simulations=num_sims,
                        num_bets=num_bets
                    )
                    
                    st.session_state.monte_carlo_results = results
                    st.success(f"✅ Simulation complete! Analyzed {num_sims:,} scenarios.")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)
        
        if st.session_state.monte_carlo_results:
            results = st.session_state.monte_carlo_results
            
            st.markdown("---")
            st.markdown("### 📊 Simulation Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Expected ROI",
                    f"{results['mean_roi']:.2f}%",
                    delta=f"{results['mean_roi'] - results['historical_roi']:.2f}% vs historical"
                )
            
            with col2:
                st.metric(
                    "90% Confidence",
                    f"{results['roi_5th_percentile']:.1f}% to {results['roi_95th_percentile']:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Probability of Profit",
                    f"{results['prob_profit']:.1f}%"
                )
            
            with col4:
                st.metric(
                    "Expected Profit",
                    f"+{results['mean_profit']:.1f} units"
                )
            
            st.markdown("---")
            st.markdown("### ⚠️ Risk Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Mean Max Drawdown", f"{results['mean_drawdown']:.2f} units")
            with col2:
                st.metric("95th Percentile DD", f"{results['drawdown_95th_percentile']:.2f} units")
            with col3:
                st.metric("Worst Case DD", f"{results['max_drawdown']:.2f} units")
            
            simulator = MonteCarloSimulator('config')
            bankroll = simulator.calculate_bankroll_requirements(results)
            
            st.info(f"💰 **Recommended Bankroll**: {bankroll['recommended_bankroll']:.1f} units | " +
                   f"With 95% confidence, max drawdown won't exceed {bankroll['drawdown_95th_percentile']:.1f} units")
            
            st.markdown("---")
            st.markdown("### 📈 Visual Analysis")
            
            fig = simulator.create_visualizations(results)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📋 Detailed Statistics"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Historical Performance:**")
                    st.write(f"- Sample Size: {results['historical_sample']} bets")
                    st.write(f"- ROI: {results['historical_roi']:.2f}%")
                    st.write(f"- Strike Rate: {results['historical_sr']:.2f}%")
                    
                    st.markdown("**Expected ROI:**")
                    st.write(f"- Mean: {results['mean_roi']:.2f}%")
                    st.write(f"- Median: {results['median_roi']:.2f}%")
                    st.write(f"- 5th Percentile: {results['roi_5th_percentile']:.2f}%")
                    st.write(f"- 95th Percentile: {results['roi_95th_percentile']:.2f}%")
                
                with col2:
                    st.markdown("**Expected Profit:**")
                    st.write(f"- Mean: {results['mean_profit']:.2f} units")
                    st.write(f"- Min: {results['min_profit']:.2f} units")
                    st.write(f"- Max: {results['max_profit']:.2f} units")
                    
                    st.markdown("**Risk Metrics:**")
                    st.write(f"- Mean DD: {results['mean_drawdown']:.2f} units")
                    st.write(f"- 95th DD: {results['drawdown_95th_percentile']:.2f} units")
                    st.write(f"- Max DD: {results['max_drawdown']:.2f} units")
    
    with tab2:
        st.markdown("### Analyze Full Portfolio (All 45 Configurations)")
        
        st.info("""
        Run Monte Carlo on all 45 systems simultaneously.
        
        **What you'll get:**
        - Portfolio-level expected ROI
        - Total drawdown risk  
        - Probability of profit
        - System rankings
        
        ⏱️ **Time:** 1-2 minutes
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            portfolio_sims = st.selectbox("Number of Simulations", [1000, 2000, 5000], index=0)
        
        with col2:
            bets_per_system = st.selectbox("Bets per System", [10, 20, 50], index=1)
        
        if st.button("🎲 Run Full Portfolio Analysis", type="primary"):
            with st.spinner(f"Analyzing all 45 configurations... This will take 1-2 minutes..."):
                try:
                    simulator = MonteCarloSimulator('config')
                    portfolio_results = simulator.simulate_portfolio(
                        num_simulations=portfolio_sims,
                        num_bets_per_system=bets_per_system
                    )
                    
                    st.success("✅ Portfolio analysis complete!")
                    
                    st.markdown("### 📊 Portfolio Performance")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Portfolio ROI", f"{portfolio_results['portfolio_mean_roi']:.2f}%")
                    with col2:
                        st.metric("90% Confidence", 
                                f"{portfolio_results['portfolio_roi_5th']:.1f}% to {portfolio_results['portfolio_roi_95th']:.1f}%")
                    with col3:
                        st.metric("Prob of Profit", f"{portfolio_results['portfolio_prob_profit']:.1f}%")
                    with col4:
                        st.metric("Expected Profit", f"+{portfolio_results['portfolio_mean_profit']:.1f} units")
                    
                    st.markdown("---")
                    st.markdown("### ⚠️ Portfolio Risk")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Bets/Sim", portfolio_results['total_bets_per_sim'])
                    with col2:
                        st.metric("Configurations", portfolio_results['num_configs'])
                    with col3:
                        st.metric("Max Portfolio DD", f"{portfolio_results['portfolio_max_drawdown']:.1f} units")
                    
                    st.markdown("---")
                    st.markdown("### 🏆 System Rankings")
                    
                    system_data = []
                    for config in portfolio_results['configs']:
                        system_data.append({
                            'System': config['system'],
                            'League': config['league'],
                            'Expected ROI': config['mean_roi'],
                            'Prob Profit': config['prob_profit'],
                            'Mean DD': config['mean_drawdown'],
                            'Historical ROI': config['historical_roi']
                        })
                    
                    systems_df = pd.DataFrame(system_data)
                    systems_df = systems_df.sort_values('Expected ROI', ascending=False)
                    
                    st.markdown("#### Top 10 Systems by Expected ROI")
                    st.dataframe(
                        systems_df.head(10).style.format({
                            'Expected ROI': '{:.2f}%',
                            'Prob Profit': '{:.1f}%',
                            'Mean DD': '{:.2f}',
                            'Historical ROI': '{:.2f}%'
                        }),
                        use_container_width=True
                    )
                    
                    st.markdown("### 📈 Portfolio ROI Distribution")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=portfolio_results['all_portfolio_rois'],
                        nbinsx=50,
                        marker_color='#366092',
                        name='Portfolio ROI'
                    ))
                    fig.add_vline(
                        x=portfolio_results['portfolio_mean_roi'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Mean: {portfolio_results['portfolio_mean_roi']:.2f}%"
                    )
                    fig.update_layout(
                        title="Distribution of Portfolio ROI Outcomes",
                        xaxis_title="ROI (%)",
                        yaxis_title="Frequency",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)

elif page == "📥 Database Upload":
    st.markdown('<div class="main-header">📥 Database Upload</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Update historical data and refresh system statistics</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### How to Update Your Database
    
    Upload your complete historical match database to:
    - ✅ Update all system statistics
    - ✅ Recalculate ROI and strike rates
    - ✅ Refresh performance charts
    - ✅ Update value scoring calculations
    
    **Required columns in your file:**
    - Date, League, Home Team, Away Team, Season
    - Home Back Odds, O2.5 Back Odds, O3.5 Lay Odds, U1.5 Lay Odds, FHGU0.5 Lay Odds
    - FTR (Full Time Result: H/D/A)
    - FTHG (Full Time Home Goals)
    - FTAG (Full Time Away Goals)
    """)
    
    uploaded_db = st.file_uploader(
        "Upload Historical Database (Excel)",
        type=['xlsx'],
        help="Upload your complete historical match database"
    )
    
    if uploaded_db is not None:
        st.info(f"📁 File uploaded: {uploaded_db.name} ({uploaded_db.size:,} bytes)")
        
        # SINGLE BUTTON - No nested buttons!
        if st.button("🔄 Process Database and Update All Statistics", type="primary"):
            with st.spinner("Processing historical database and recalculating statistics... This may take 1-2 minutes..."):
                try:
                    # Save file
                    db_file = Path("data/historical_matches.xlsx")
                    db_file.parent.mkdir(exist_ok=True)
                    
                    with open(db_file, "wb") as f:
                        f.write(uploaded_db.getbuffer())
                    
                    # Load and validate
                    historical = pd.read_excel(db_file, header=1, engine='openpyxl')
                    
                    st.success(f"✅ Loaded {len(historical):,} historical matches")
                    
                    # Show sample
                    st.markdown("#### Sample Data (First 5 Rows)")
                    sample_cols = ['Date', 'Competition', 'Home Team', 'Away Team', 'FTR', 'FTHG', 'FTAG']
                    
                    # Handle League vs Competition column
                    if 'Competition' in historical.columns:
                        display_cols = sample_cols
                    elif 'League' in historical.columns:
                        display_cols = [col.replace('Competition', 'League') if col == 'Competition' else col for col in sample_cols]
                    else:
                        display_cols = [col for col in sample_cols if col in historical.columns]
                    
                    available_cols = [col for col in display_cols if col in historical.columns]
                    st.dataframe(historical.head()[available_cols], use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("### Recalculating System Statistics...")
                    
                    # Process database immediately (no second button)
                    from models.database_processor import DatabaseProcessor
                    
                    processor = DatabaseProcessor('config')
                    stats = processor.update_from_database(str(db_file))
                    
                    # CRITICAL: Store in session state (Streamlit Cloud compatible)
                    st.session_state.portfolio_stats = stats
                    
                    # Try to save to file (may fail on read-only filesystem - that's OK)
                    try:
                        with open('config/portfolio_stats.json', 'w') as f:
                            json.dump(stats, f, indent=2)
                    except:
                        pass  # Silently ignore if filesystem is read-only
                    
                    st.success("✅ Database processed and statistics updated!")
                    st.balloons()
                    
                    st.markdown("### Updated Statistics Summary")
                    st.write(f"Total configurations: {len(stats['stats'])}")
                    st.write(f"Max ROI: {stats['max_roi']:.2f}%")
                    st.write(f"Total bets: {sum(s['total_bets'] for s in stats['stats'].values()):,}")
                    
                    # Reinitialize selector with new data
                    st.session_state.selector = DailyBetSelector('config')
                    
                    # Clear monte carlo results
                    if 'monte_carlo_results' in st.session_state:
                        st.session_state.monte_carlo_results = None
                    
                    st.info("🔄 Refreshing all tabs with updated data...")
                    
                    # Force rerun
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing database: {str(e)}")
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    Football Betting Model v1.0 | Built with Streamlit | © 2026
</div>
""", unsafe_allow_html=True)
