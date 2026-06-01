"""
FTS Odds Portfolio Dashboard
Streamlit dashboard for the Football Trading Systems Odds Portfolio.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from pathlib import Path
from io import BytesIO

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FTS Odds Portfolio",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg,#1F3864,#2E75B6);
        border-radius:10px; padding:16px; text-align:center; color:#fff;
        margin-bottom:8px;
    }
    .metric-val { font-size:1.8rem; font-weight:700; }
    .metric-lbl { font-size:0.85rem; opacity:0.85; margin-top:2px; }
    .bet-card-exact {
        background:#C6EFCE; border-left:5px solid #375623;
        border-radius:6px; padding:10px 14px; margin-bottom:6px;
    }
    .bet-card-buffer {
        background:#FFEB9C; border-left:5px solid #9C5700;
        border-radius:6px; padding:10px 14px; margin-bottom:6px;
    }
    div[data-testid="stMetricValue"] { font-size:1.4rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SYS_ORDER  = ["FHGU0.5 Lay","U1.5 Lay","O3.5 Lay","O2.5 Back","Home Win"]
SYS_COLORS = {
    "FHGU0.5 Lay":"#1F3864","U1.5 Lay":"#2E75B6","O3.5 Lay":"#375623",
    "O2.5 Back":"#7B3F00","Home Win":"#6B2D8B",
}
BET_TYPE = {
    "FHGU0.5 Lay":"LAY","U1.5 Lay":"LAY","O3.5 Lay":"LAY",
    "O2.5 Back":"BACK","Home Win":"BACK",
}
MARKET_COLS = {
    "FHGU0.5 Lay":"FHGU0.5 Lay Odds","U1.5 Lay":"U1.5 Lay Odds",
    "O3.5 Lay":"O3.5 Lay Odds","O2.5 Back":"O2.5 Back Odds",
    "Home Win":"Home Back Odds",
}

# ── Load config ───────────────────────────────────────────────────────────────
@st.cache_data
def load_portfolio():
    with open("config/portfolio_stats.json") as f:
        raw = json.load(f)
    rows = []
    for stat in raw["stats"].values():
        rows.append({
            "system": stat["system"], "league": stat["league"],
            "bets": stat["total_bets"], "sr": stat["strike_rate"],
            "roi": stat["roi"], "profit": stat["profit"],
        })
    return pd.DataFrame(rows), raw["max_roi"]

@st.cache_data
def load_systems_config():
    with open("config/systems_config.json") as f:
        return json.load(f)

df_all, max_roi = load_portfolio()
cfg = load_systems_config()

# System-level summary
summary = (
    df_all.groupby("system")
    .agg(bets=("bets","sum"), profit=("profit","sum"))
    .reset_index()
)
summary["roi"] = summary["profit"] / summary["bets"] * 100
summary["sr"]  = df_all.groupby("system")["sr"].mean().reset_index()["sr"]
order_map = {s:i for i,s in enumerate(SYS_ORDER)}
summary["_ord"] = summary["system"].map(order_map)
summary = summary.sort_values("_ord").drop("_ord",axis=1).reset_index(drop=True)

port_bets   = int(summary["bets"].sum())
port_profit = summary["profit"].sum()
port_roi    = port_profit / port_bets * 100

# ── Daily selector engine (self-contained) ────────────────────────────────────
def scan_fixtures(fixtures_df: pd.DataFrame) -> list[dict]:
    """
    Apply all 5 system rules to a fixtures dataframe.
    Returns list of qualifying bets.

    Supports the FTSAdvanced-PreMatch.xlsx format (header=1):
      Competition, Home Team, Away Team, Date, Time
      FHGU0.5 Lay odds → 'FHGU0.5.1'
      U1.5 Lay odds    → 'U1.5.1'
      O3.5 Lay odds    → 'O3.5.1'
      O2.5 Back odds   → 'Over 2.5 Back'
      Home Win Back    → 'Home Win Back'
      Home Back (filter) → 'Home Win Back'
    Also handles generic uploads with standard column names.
    """
    cols = fixtures_df.columns.tolist()

    # ── Map to internal names ──────────────────────────────────────────────
    def find_col(*candidates):
        for c in candidates:
            if c in cols:
                return c
        return None

    competition_col = find_col("Competition","League","competition","league")
    home_col        = find_col("Home Team","home_team","Home","home")
    away_col        = find_col("Away Team","away_team","Away","away")
    date_col        = find_col("Date","date")
    time_col        = find_col("Time","time","Kick Off","kickoff")

    # Odds: FTSAdvanced-PreMatch format first, then generic fallback
    ODDS_COLS = {
        "FHGU0.5 Lay": find_col("FHGU0.5.1","FHGU0.5","FHGU0.5 Lay Odds"),
        "U1.5 Lay":    find_col("U1.5.1","U1.5","U1.5 Lay Odds"),
        "O3.5 Lay":    find_col("O3.5.1","O3.5","O3.5 Lay Odds"),
        "O2.5 Back":   find_col("Over 2.5 Back","O2.5","O2.5 Back Odds"),
        "Home Win":    find_col("Home Win Back","Home Back Odds"),
    }
    HOME_BACK_COL = find_col("Home Win Back","Home Back Odds","Home Odds")

    qualifying = []

    for _, row in fixtures_df.iterrows():
        league = str(row[competition_col]) if competition_col and pd.notna(row[competition_col]) else ""
        home   = str(row[home_col])        if home_col        and pd.notna(row[home_col])        else ""
        away   = str(row[away_col])        if away_col        and pd.notna(row[away_col])        else ""
        date   = row[date_col]             if date_col        else ""
        time   = row[time_col]             if time_col        else ""

        if not league or league in ("nan","None",""):
            continue

        for sys_name in SYS_ORDER:
            sys_cfg    = cfg[sys_name]
            odds_col   = ODDS_COLS[sys_name]
            if odds_col is None:
                continue
            odds = row.get(odds_col)

            if odds is None or (isinstance(odds, float) and np.isnan(odds)):
                continue
            try:
                odds = float(odds)
            except (ValueError, TypeError):
                continue

            # Find league config
            lc = next((c for c in sys_cfg["configurations"] if c["league"] == league), None)
            if lc is None:
                continue

            in_exact  = lc["exact_min"]  <= odds <= lc["exact_max"]
            in_buffer = lc["buffer_min"] <= odds <= lc["buffer_max"]

            if not (in_exact or in_buffer):
                continue

            # O2.5 Back filter: Home Back Odds > 2.00
            filter_note = ""
            if sys_cfg.get("has_filter") and sys_cfg.get("filter_condition"):
                home_odds = row.get(HOME_BACK_COL) if HOME_BACK_COL else None
                if home_odds is None or (isinstance(home_odds, float) and np.isnan(home_odds)):
                    continue
                try:
                    home_odds = float(home_odds)
                except (ValueError, TypeError):
                    continue
                if home_odds < 1.80:          # Below buffer min — exclude entirely
                    continue
                elif home_odds < 2.00:        # Buffer zone
                    filter_note = f"⚠️ Home odds {home_odds:.2f} (buffer, need >2.00)"
                else:
                    filter_note = f"✅ Home odds {home_odds:.2f}"

            # Look up historical league performance
            lg_row = df_all[(df_all["system"]==sys_name) & (df_all["league"]==league)]
            if len(lg_row) > 0:
                hist_roi = lg_row.iloc[0]["roi"]
                hist_bets= int(lg_row.iloc[0]["bets"])
                hist_sr  = lg_row.iloc[0]["sr"]
                hist_str = f"{hist_bets} bets | {hist_sr:.1f}% SR | {hist_roi:+.1f}% ROI"
            else:
                hist_str = "No historical data"

            qualifying.append({
                "system":     sys_name,
                "bet_type":   BET_TYPE[sys_name],
                "league":     league,
                "home":       home,
                "away":       away,
                "date":       str(date),
                "time":       str(time),
                "odds":       odds,
                "odds_range": f"{lc['exact_min']:.2f}–{lc['exact_max']:.2f}",
                "in_exact":   in_exact,
                "filter_note":filter_note,
                "history":    hist_str,
            })

    return qualifying

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ FTS Odds Portfolio")
    st.markdown("---")
    page = st.radio("Navigation", [
        "📊 Daily Selector",
        "📈 Performance",
        "🏆 System Rankings",
        "📋 League Breakdown",
        "⚙️ System Config",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### Portfolio Snapshot")
    st.metric("Total Bets",    f"{port_bets:,}")
    st.metric("Total Profit",  f"+{port_profit:.2f} pts")
    st.metric("Portfolio ROI", f"{port_roi:.2f}%")
    st.metric("Best ROI",      f"{max_roi:.2f}%")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DAILY SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Daily Selector":
    st.markdown("## 📊 Daily Bet Selector")
    st.markdown("Upload your fixtures file to find today's qualifying bets across all 5 systems.")

    st.markdown("""
    **Required columns in your file:**
    `Competition` / `League` &nbsp;|&nbsp; `Home Team` &nbsp;|&nbsp; `Away Team`
    &nbsp;|&nbsp; `Date` &nbsp;|&nbsp; `Time` *(optional)*
    &nbsp;|&nbsp; `FHGU0.5 Lay Odds` &nbsp;|&nbsp; `U1.5 Lay Odds`
    &nbsp;|&nbsp; `O3.5 Lay Odds` &nbsp;|&nbsp; `O2.5 Back Odds`
    &nbsp;|&nbsp; `Home Back Odds`
    """)

    uploaded = st.file_uploader(
        "Upload fixtures (CSV or Excel)",
        type=["csv","xlsx"],
        label_visibility="collapsed"
    )

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                fx = pd.read_csv(uploaded)
            else:
                # Try header=1 first (FTSAdvanced-PreMatch format)
                fx_try = pd.read_excel(uploaded, header=1)
                # If first column looks like 'Date' in row 0 it's a single-header file
                if "Competition" in fx_try.columns or "Competition" in fx_try.columns:
                    fx = fx_try
                elif "Date" in fx_try.columns and "Competition" in fx_try.columns:
                    fx = fx_try
                else:
                    # Fall back to header=0 for standard files
                    uploaded.seek(0)
                    fx = pd.read_excel(uploaded, header=0)
            # Drop any row where Competition is NaN or looks like a header repeat
            if "Competition" in fx.columns:
                fx = fx[fx["Competition"].notna()]
                fx = fx[fx["Competition"] != "Competition"]
            st.success(f"✅ Loaded **{len(fx):,} fixtures** from {uploaded.name}")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        bets = scan_fixtures(fx)

        if not bets:
            st.warning("No qualifying bets found. Check that your odds columns match the required names.")
        else:
            exact_bets  = [b for b in bets if b["in_exact"]]
            buffer_bets = [b for b in bets if not b["in_exact"]]

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Qualifying", len(bets))
            c2.metric("✅ Exact Range",   len(exact_bets))
            c3.metric("⚠️ Buffer Zone",   len(buffer_bets))
            systems_hit = len({b["system"] for b in bets})
            c4.metric("Systems Triggered", f"{systems_hit}/5")

            st.markdown("---")

            # Filter controls
            f1,f2 = st.columns(2)
            with f1:
                sys_filter = st.multiselect(
                    "Filter by System", SYS_ORDER,
                    default=SYS_ORDER, key="ds_sys"
                )
            with f2:
                zone_filter = st.multiselect(
                    "Odds Zone",
                    ["✅ Exact Range","⚠️ Buffer Zone"],
                    default=["✅ Exact Range","⚠️ Buffer Zone"],
                    key="ds_zone"
                )

            show_exact  = "✅ Exact Range"  in zone_filter
            show_buffer = "⚠️ Buffer Zone" in zone_filter

            filtered = [
                b for b in bets
                if b["system"] in sys_filter
                and ((show_exact and b["in_exact"]) or (show_buffer and not b["in_exact"]))
            ]

            st.markdown(f"### Showing {len(filtered)} bets")

            for b in filtered:
                card_class = "bet-card-exact" if b["in_exact"] else "bet-card-buffer"
                zone_label = "✅ EXACT RANGE" if b["in_exact"] else "⚠️ BUFFER ZONE"
                sys_color  = SYS_COLORS.get(b["system"],"#333")
                filter_html = f"<br><small>{b['filter_note']}</small>" if b["filter_note"] else ""

                st.markdown(f"""
                <div class="{card_class}">
                    <b>{b['home']} vs {b['away']}</b>
                    &nbsp;<span style="color:#666;font-size:0.9rem">{b['league']} &nbsp;|&nbsp; {b['date']} {b['time']}</span><br>
                    <span style="background:{sys_color};color:#fff;border-radius:4px;
                          padding:1px 8px;font-size:0.85rem;font-weight:600">
                        {b['bet_type']} — {b['system']}
                    </span>
                    &nbsp;&nbsp;<b>Odds: {b['odds']:.2f}</b>
                    &nbsp;(Range: {b['odds_range']})
                    &nbsp;&nbsp;<span style="font-size:0.85rem">{zone_label}</span>
                    {filter_html}
                    <br><small style="color:#555">📊 History: {b['history']}</small>
                </div>
                """, unsafe_allow_html=True)

            # Export
            st.markdown("---")
            if st.button("📥 Export to Excel"):
                out_df = pd.DataFrame([{
                    "Date": b["date"], "Time": b["time"],
                    "League": b["league"],
                    "Home": b["home"], "Away": b["away"],
                    "System": b["system"], "Bet Type": b["bet_type"],
                    "Odds": b["odds"], "Range": b["odds_range"],
                    "Zone": "Exact" if b["in_exact"] else "Buffer",
                    "Filter": b["filter_note"],
                    "Historical Performance": b["history"],
                } for b in filtered])

                buf = BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    out_df.to_excel(writer, index=False, sheet_name="Daily Bets")
                buf.seek(0)
                st.download_button(
                    "⬇️ Download Excel",
                    data=buf,
                    file_name="fts_daily_selections.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    else:
        st.info("👆 Upload a fixtures file above to generate today's selections.")
        st.markdown("---")
        st.markdown("### System Odds Ranges (Quick Reference)")
        for sys in SYS_ORDER:
            sc = SYS_COLORS.get(sys,"#333")
            leagues = cfg[sys]["configurations"]
            with st.expander(f"{sys} — {len(leagues)} leagues"):
                ref_df = pd.DataFrame([{
                    "League": lc["league"],
                    "Exact Min": lc["exact_min"],
                    "Exact Max": lc["exact_max"],
                    "Buffer Min": lc["buffer_min"],
                    "Buffer Max": lc["buffer_max"],
                } for lc in leagues])
                st.dataframe(ref_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Performance":
    st.markdown("## 📈 Portfolio Performance")

    cols = st.columns(5)
    for i, row in summary.iterrows():
        color = SYS_COLORS.get(row["system"],"#1F3864")
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="background:linear-gradient(135deg,{color},{color}bb);">
                <div class="metric-val">{row["roi"]:+.1f}%</div>
                <div class="metric-lbl">{row["system"]}</div>
                <div class="metric-lbl">{int(row["bets"]):,} bets &nbsp;|&nbsp; +{row["profit"]:.1f}pts</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### System Totals")
    tbl = summary[["system","bets","sr","profit","roi"]].copy()
    tbl.columns = ["System","Bets","SR %","Profit","ROI %"]
    tbl["ROI %"]  = tbl["ROI %"].map("{:+.2f}%".format)
    tbl["SR %"]   = tbl["SR %"].map("{:.2f}%".format)
    tbl["Profit"] = tbl["Profit"].map("{:+.2f}".format)
    tbl["Bets"]   = tbl["Bets"].map("{:,}".format)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

    st.markdown("---")
    c1,c2 = st.columns(2)

    with c1:
        st.markdown("### ROI by System")
        fig = go.Figure()
        for _, row in summary.iterrows():
            fig.add_trace(go.Bar(
                x=[row["system"]], y=[row["roi"]],
                marker_color=SYS_COLORS.get(row["system"],"#1F3864"),
                text=f'{row["roi"]:+.2f}%', textposition="outside",
                showlegend=False,
            ))
        fig.update_layout(
            height=340, yaxis_title="ROI %",
            plot_bgcolor="white", yaxis=dict(gridcolor="#eee"),
            margin=dict(t=20,b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### Profit Share")
        fig2 = go.Figure(go.Pie(
            labels=summary["system"], values=summary["profit"],
            marker_colors=[SYS_COLORS.get(s,"#aaa") for s in summary["system"]],
            hole=0.45, textinfo="label+percent",
        ))
        fig2.update_layout(height=340, margin=dict(t=20,b=10), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 System Rankings":
    st.markdown("## 🏆 System Rankings")

    sys_sel = st.selectbox("Select System", SYS_ORDER)
    sys_df  = df_all[df_all["system"]==sys_sel].copy()
    sys_tot = summary[summary["system"]==sys_sel].iloc[0]

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Bets",   f"{int(sys_tot['bets']):,}")
    c2.metric("Total Profit", f"+{sys_tot['profit']:.2f} pts")
    c3.metric("ROI",          f"{sys_tot['roi']:+.2f}%")
    c4.metric("Avg SR",       f"{sys_tot['sr']:.2f}%")

    st.markdown("---")
    st.markdown("### League Rankings by ROI")
    sys_df = sys_df.sort_values("roi", ascending=False)
    fig = go.Figure(go.Bar(
        x=sys_df["roi"], y=sys_df["league"], orientation="h",
        marker_color=[
            "#375623" if r>20 else "#2E75B6" if r>10 else "#FFC000" if r>0 else "#C00000"
            for r in sys_df["roi"]
        ],
        text=sys_df["roi"].map("{:+.1f}%".format), textposition="outside",
    ))
    fig.update_layout(
        height=max(300, len(sys_df)*32), xaxis_title="ROI %",
        plot_bgcolor="white", xaxis=dict(gridcolor="#eee"),
        margin=dict(t=10,b=10,l=10,r=80),
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Detail Table")
    disp = sys_df[["league","bets","sr","profit","roi"]].copy()
    disp.columns = ["League","Bets","SR %","Profit","ROI %"]
    disp["ROI %"]  = disp["ROI %"].map("{:+.2f}%".format)
    disp["SR %"]   = disp["SR %"].map("{:.2f}%".format)
    disp["Profit"] = disp["Profit"].map("{:+.2f}".format)
    disp["Bets"]   = disp["Bets"].map("{:,}".format)
    st.dataframe(disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LEAGUE BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 League Breakdown":
    st.markdown("## 📋 League Breakdown — All Systems")

    top_leagues = df_all.groupby("league")["bets"].sum().nlargest(15).index.tolist()
    hm = df_all[df_all["league"].isin(top_leagues)].pivot_table(
        index="league", columns="system", values="roi", aggfunc="sum"
    ).fillna(0).reindex(columns=SYS_ORDER, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=hm.values, x=hm.columns.tolist(), y=hm.index.tolist(),
        colorscale=[[0,"#C00000"],[0.4,"#FF9999"],[0.5,"#FFFFFF"],[0.7,"#9DC3E6"],[1,"#1F3864"]],
        text=[[f"{v:+.1f}%" for v in row] for row in hm.values],
        texttemplate="%{text}", colorbar=dict(title="ROI %"),
    ))
    fig.update_layout(
        height=500, margin=dict(t=20,b=20,l=180,r=20),
        xaxis_title="", yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sys_filter = st.multiselect("Filter by System", SYS_ORDER, default=SYS_ORDER)
    filt = df_all[df_all["system"].isin(sys_filter)].sort_values(["system","roi"],ascending=[True,False]).copy()
    filt.columns = [c.title() for c in filt.columns]
    filt["Roi"]    = filt["Roi"].map("{:+.2f}%".format)
    filt["Sr"]     = filt["Sr"].map("{:.2f}%".format)
    filt["Profit"] = filt["Profit"].map("{:+.2f}".format)
    filt["Bets"]   = filt["Bets"].map("{:,}".format)
    filt = filt.rename(columns={"Roi":"ROI %","Sr":"SR %","System":"System","League":"League"})
    st.dataframe(filt[["System","League","Bets","SR %","Profit","ROI %"]],
                 use_container_width=True, hide_index=True, height=500)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM CONFIG
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ System Config":
    st.markdown("## ⚙️ System Configuration")

    sys_sel = st.selectbox("Select System", SYS_ORDER)
    sc      = cfg[sys_sel]
    row     = summary[summary["system"]==sys_sel].iloc[0]

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### System Details")
        st.write(f"**Market column:** `{sc['market_column']}`")
        st.write(f"**Bet type:** {BET_TYPE[sys_sel]}")
        st.write(f"**Has filter:** {sc['has_filter']}")
        if sc["has_filter"]:
            st.write(f"**Filter:** `{sc['filter_condition']}`")
        st.write(f"**Leagues configured:** {len(sc['configurations'])}")
    with c2:
        st.markdown("### System Performance")
        st.metric("Total Bets",   f"{int(row['bets']):,}")
        st.metric("Total Profit", f"+{row['profit']:.2f} pts")
        st.metric("ROI",          f"{row['roi']:+.2f}%")
        st.metric("Avg SR",       f"{row['sr']:.2f}%")

    st.markdown("---")
    st.markdown("### League Configurations")
    cfg_df = pd.DataFrame(sc["configurations"]).rename(columns={
        "league":"League","exact_min":"Exact Min","exact_max":"Exact Max",
        "buffer_min":"Buffer Min","buffer_max":"Buffer Max",
    })
    st.dataframe(cfg_df, use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;'>"
    "FTS Odds Portfolio &nbsp;|&nbsp; Updated Jun 2026 &nbsp;|&nbsp; 6,582 bets &nbsp;|&nbsp; 18.18% ROI"
    "</div>",
    unsafe_allow_html=True,
)
