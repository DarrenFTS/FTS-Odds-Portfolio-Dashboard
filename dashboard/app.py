"""
FTS Odds Portfolio Dashboard
Streamlit dashboard for the Football Trading Systems Odds Portfolio.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path

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
    }
    .metric-val  { font-size:1.8rem; font-weight:700; }
    .metric-lbl  { font-size:0.85rem; opacity:0.85; margin-top:2px; }
    .sys-card    { border-radius:8px; padding:12px 16px; margin-bottom:6px; }
    div[data-testid="stMetricValue"] { font-size:1.4rem; }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_portfolio():
    with open("config/portfolio_stats.json") as f:
        raw = json.load(f)
    rows = []
    for key, stat in raw["stats"].items():
        rows.append({
            "system":  stat["system"],
            "league":  stat["league"],
            "bets":    stat["total_bets"],
            "sr":      stat["strike_rate"],
            "roi":     stat["roi"],
            "profit":  stat["profit"],
        })
    df = pd.DataFrame(rows)
    return df, raw["max_roi"]

@st.cache_data
def load_systems_config():
    with open("config/systems_config.json") as f:
        return json.load(f)

df_all, max_roi = load_portfolio()
cfg = load_systems_config()

# ── System-level summary ───────────────────────────────────────────────────────
SYS_ORDER  = ["FHGU0.5 Lay","U1.5 Lay","O3.5 Lay","O2.5 Back","Home Win"]
SYS_COLORS = {
    "FHGU0.5 Lay": "#1F3864",
    "U1.5 Lay":    "#2E75B6",
    "O3.5 Lay":    "#375623",
    "O2.5 Back":   "#7B3F00",
    "Home Win":    "#6B2D8B",
}

summary = (
    df_all.groupby("system")
    .agg(bets=("bets","sum"), profit=("profit","sum"))
    .reset_index()
)
summary["roi"]    = summary["profit"] / summary["bets"] * 100
summary["sr"]     = df_all.groupby("system")["sr"].mean().values
summary["sys_order"] = summary["system"].map({s:i for i,s in enumerate(SYS_ORDER)})
summary = summary.sort_values("sys_order").drop("sys_order",axis=1).reset_index(drop=True)

port_bets   = int(summary["bets"].sum())
port_profit = summary["profit"].sum()
port_roi    = port_profit / port_bets * 100

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ FTS Odds Portfolio")
    st.markdown("---")
    page = st.radio("Navigation", [
        "📈 Performance",
        "🏆 System Rankings",
        "📋 League Breakdown",
        "⚙️ System Config",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 📊 Portfolio Snapshot")
    st.metric("Total Bets",   f"{port_bets:,}")
    st.metric("Total Profit", f"+{port_profit:.2f} pts")
    st.metric("Portfolio ROI",f"{port_roi:.2f}%")
    st.metric("Best System ROI", f"{max_roi:.2f}%")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
if page == "📈 Performance":
    st.markdown("## 📈 Portfolio Performance")

    # Top KPI row
    cols = st.columns(5)
    for i, row in summary.iterrows():
        with cols[i]:
            color = SYS_COLORS.get(row["system"],"#1F3864")
            st.markdown(f"""
            <div class="metric-card" style="background:linear-gradient(135deg,{color},{color}cc);">
                <div class="metric-val">{row["roi"]:+.1f}%</div>
                <div class="metric-lbl">{row["system"]}</div>
                <div class="metric-lbl">{int(row["bets"]):,} bets &nbsp;|&nbsp; +{row["profit"]:.1f} pts</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Summary table
    st.markdown("### System Totals")
    tbl = summary.copy()
    tbl["ROI %"]     = tbl["roi"].map("{:+.2f}%".format)
    tbl["SR %"]      = tbl["sr"].map("{:.2f}%".format)
    tbl["Profit"]    = tbl["profit"].map("{:+.2f}".format)
    tbl["Bets"]      = tbl["bets"].map("{:,}".format)
    tbl = tbl.rename(columns={"system":"System"})
    st.dataframe(
        tbl[["System","Bets","SR %","Profit","ROI %"]],
        use_container_width=True, hide_index=True
    )

    st.markdown("---")

    # Bar chart – ROI by system
    st.markdown("### ROI by System")
    fig_bar = go.Figure()
    for _, row in summary.iterrows():
        color = SYS_COLORS.get(row["system"],"#1F3864")
        fig_bar.add_trace(go.Bar(
            x=[row["system"]], y=[row["roi"]],
            marker_color=color, name=row["system"],
            text=f'{row["roi"]:+.2f}%', textposition="outside",
        ))
    fig_bar.update_layout(
        showlegend=False, height=350,
        yaxis_title="ROI %", xaxis_title="",
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eee"),
        margin=dict(t=20,b=20),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Profit by system
    st.markdown("### Profit Contribution (pts)")
    fig_pie = go.Figure(go.Pie(
        labels=summary["system"],
        values=summary["profit"],
        marker_colors=[SYS_COLORS.get(s,"#aaa") for s in summary["system"]],
        hole=0.45,
        textinfo="label+percent",
    ))
    fig_pie.update_layout(height=360, margin=dict(t=20,b=20), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 System Rankings":
    st.markdown("## 🏆 System Rankings")

    sys_sel = st.selectbox("Select System", SYS_ORDER)
    sys_df  = df_all[df_all["system"]==sys_sel].copy()
    sys_tot = summary[summary["system"]==sys_sel].iloc[0]

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Bets",  f"{int(sys_tot['bets']):,}")
    c2.metric("Total Profit",f"+{sys_tot['profit']:.2f} pts")
    c3.metric("ROI",         f"{sys_tot['roi']:+.2f}%")
    c4.metric("Avg SR",      f"{sys_tot['sr']:.2f}%")

    st.markdown("---")
    st.markdown("### League Rankings by ROI")

    sys_df_sorted = sys_df.sort_values("roi", ascending=False).reset_index(drop=True)
    sys_df_sorted["rank"] = sys_df_sorted.index + 1

    # Horizontal bar chart
    fig_h = go.Figure(go.Bar(
        x=sys_df_sorted["roi"],
        y=sys_df_sorted["league"],
        orientation="h",
        marker_color=[
            "#375623" if r>20 else "#2E75B6" if r>10 else "#FFC000" if r>0 else "#C00000"
            for r in sys_df_sorted["roi"]
        ],
        text=sys_df_sorted["roi"].map("{:+.1f}%".format),
        textposition="outside",
    ))
    fig_h.update_layout(
        height=max(300, len(sys_df_sorted)*35),
        xaxis_title="ROI %", yaxis_title="",
        plot_bgcolor="white", xaxis=dict(gridcolor="#eee"),
        margin=dict(t=10,b=10,l=10,r=80),
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("### Detail Table")
    disp = sys_df_sorted[["league","bets","sr","profit","roi"]].copy()
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

    # Heatmap: ROI per system × league (top 15 leagues by total bets)
    top_leagues = (
        df_all.groupby("league")["bets"].sum()
        .nlargest(15).index.tolist()
    )
    hm_df = df_all[df_all["league"].isin(top_leagues)].copy()
    pivot  = hm_df.pivot_table(index="league", columns="system",
                                values="roi", aggfunc="sum").fillna(0)
    pivot  = pivot.reindex(columns=SYS_ORDER, fill_value=0)

    fig_hm = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0,"#C00000"],[0.4,"#FF9999"],
            [0.5,"#FFFFFF"],
            [0.7,"#9DC3E6"],[1.0,"#1F3864"],
        ],
        text=[[f"{v:+.1f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hoverongaps=False,
        colorbar=dict(title="ROI %"),
    ))
    fig_hm.update_layout(
        height=500, margin=dict(t=20,b=20,l=160,r=20),
        xaxis_title="", yaxis_title="",
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    st.markdown("---")
    st.markdown("### Full Table — Filter by System")

    sys_filter = st.multiselect(
        "Systems", SYS_ORDER, default=SYS_ORDER,
        key="lb_sys"
    )
    filtered = df_all[df_all["system"].isin(sys_filter)].copy()
    filtered = filtered.sort_values(["system","roi"], ascending=[True,False])
    filtered = filtered.rename(columns={
        "system":"System","league":"League",
        "bets":"Bets","sr":"SR %","roi":"ROI %","profit":"Profit"
    })
    filtered["ROI %"]  = filtered["ROI %"].map("{:+.2f}%".format)
    filtered["SR %"]   = filtered["SR %"].map("{:.2f}%".format)
    filtered["Profit"] = filtered["Profit"].map("{:+.2f}".format)
    filtered["Bets"]   = filtered["Bets"].map("{:,}".format)
    st.dataframe(filtered[["System","League","Bets","SR %","Profit","ROI %"]],
                 use_container_width=True, hide_index=True, height=500)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM CONFIG
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ System Config":
    st.markdown("## ⚙️ System Configuration")

    sys_sel = st.selectbox("Select System", SYS_ORDER)
    sc      = cfg[sys_sel]

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### System Details")
        st.write(f"**Market column:** `{sc['market_column']}`")
        st.write(f"**Has filter:** {sc['has_filter']}")
        if sc["has_filter"]:
            st.write(f"**Filter condition:** `{sc['filter_condition']}`")
        st.write(f"**Leagues configured:** {len(sc['configurations'])}")

    with c2:
        st.markdown("### System Performance")
        row = summary[summary["system"]==sys_sel].iloc[0]
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
    "<div style=\'text-align:center;color:#888;font-size:0.85rem;\'>"
    "FTS Odds Portfolio Dashboard &nbsp;|&nbsp; Updated Jun 2026"
    "</div>",
    unsafe_allow_html=True,
)
