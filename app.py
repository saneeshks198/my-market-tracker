import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# 1. Page Configuration (Terminal Theme)
st.set_page_config(page_title="Professional RRG Terminal", layout="wide")
st.title("🏛️ Institutional Relative Rotation Graph Terminal")
st.caption("De Kempenaer Rotation Model with clean historical vector paths and canvas quadrant shading.")

# 2. Controls & Sidebar Setup
st.sidebar.header("🎛️ Terminal Configuration")
market = st.sidebar.selectbox("Market Universe", ["US Market 🇺🇸", "Indian Market 🇮🇳"])
interval = st.sidebar.selectbox("Data Interval", ["1wk", "1d"])
trail_periods = st.sidebar.slider("Historical Trail Length (Bars)", min_value=4, max_value=24, value=8)

if market == "US Market 🇺🇸":
    benchmark = "^GSPC"  # S&P 500 Index
    universe = {
        "Technology (XLK)": "XLK", 
        "Financials (XLF)": "XLF", 
        "Healthcare (XLV)": "XLV", 
        "Energy (XLE)": "XLE", 
        "Consumer Discretionary (XLY)": "XLY", 
        "Industrials (XLI)": "XLI"
    }
else:
    benchmark = "^NSEI"  # Nifty 50 Index
    # Utilizing liquid NSE ETFs to guarantee free live data availability
    universe = {
        "Nifty Bank (BANKBEES)": "BANKBEES.NS",
        "Nifty IT (ITBEES)": "ITBEES.NS",
        "Nifty Pharma (PHARMABEES)": "PHARMABEES.NS",
        "Nifty Auto (AUTOBEES)": "AUTOBEES.NS",
        "Nifty FMCG (FMCGBEES)": "FMCGBEES.NS",
        "Nifty Infra (INFRABEES)": "INFRABEES.NS"
    }

# 3. Mathematical RRG Engine
@st.cache_data(ttl=600)
def compute_true_rrg(assets_dict, bench_ticker, data_interval, lookback_bars):
    tickers_list = list(assets_dict.values()) + [bench_ticker]
    # Fetch ample history to calculate moving matrices properly
    raw_close = yf.download(tickers_list, period="1y", interval=data_interval)['Close']
    
    if bench_ticker not in raw_close.columns or raw_close[bench_ticker].isnull().all():
        return pd.DataFrame()
        
    bench_series = raw_close[bench_ticker]
    all_points = []
    
    # Filter only tickers that successfully returned real data columns
    valid_assets = {label: ticker for label, ticker in assets_dict.items() 
                    if ticker in raw_close.columns and not raw_close[ticker].isnull().all()}
    
    if not valid_assets:
        return pd.DataFrame()

    # Step A: Compute Base Relative Strength Matrix
    df_rs = pd.DataFrame({label: (raw_close[ticker] / bench_series) * 100 
                          for label, ticker in valid_assets.items()})
    
    # Step B: JDK RS-Ratio Calculation (14-period Trend EMA)
    rs_ratio_raw = df_rs.ewm(span=14, adjust=False).mean()
    
    # Step C: JDK RS-Momentum Calculation (5-period velocity of the trend line)
    rs_momentum_raw = rs_ratio_raw.pct_change(periods=5) * 100 + 100
    
    # Step D: Z-Score Cross Normalization to balance variance around center point 100
    normalized_ratio = (rs_ratio_raw - rs_ratio_raw.mean()) / rs_ratio_raw.std() * 1.5 + 100
    normalized_momentum = (rs_momentum_raw - rs_momentum_raw.mean()) / rs_momentum_raw.std() * 1.5 + 100
    
    # Extract trailing data rows up to specified lookback depth
    available_rows = len(normalized_ratio)
    actual_lookback = min(lookback_bars, available_rows)
    
    for label in valid_assets.keys():
        for i in range(-actual_lookback, 0):
            date_str = normalized_ratio.index[i].strftime('%Y-%m-%d')
            all_points.append({
                "Asset": label,
                "Date": date_str,
                "RS_Ratio": round(normalized_ratio[label].iloc[i], 3),
                "RS_Momentum": round(normalized_momentum[label].iloc[i], 3),
                "Sequence": i + actual_lookback
            })
            
    return pd.DataFrame(all_points)

# Run Engine Calculations
with st.spinner("Downloading and compiling live market asset matrices..."):
    try:
        master_df = compute_true_rrg(universe, benchmark, interval, trail_periods)
        if master_df.empty:
            st.error("No active data returned from API. Please try switching the interval or market profile.")
            execution_error = True
        else:
            execution_error = False
    except Exception as e:
        st.error(f"Engine matrix failure: {e}")
        execution_error = True

# 4. Canvas Rendering Block
if not execution_error:
    # Safely calculate outer grid sizing bounds based on dynamic data elements
    min_x = min(master_df['RS_Ratio'].min(), 97.0) - 0.5
    max_x = max(master_df['RS_Ratio'].max(), 103.0) + 0.5
    min_y = min(master_df['RS_Momentum'].min(), 97.0) - 0.5
    max_y = max(master_df['RS_Momentum'].max(), 103.0) + 0.5
    
    fig = go.Figure()

    # Add Translucent Background Rectangles to highlight Quadrant blocks
    fig.add_shape(type="rect", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="rgba(46, 204, 113, 0.07)", line_width=0)   # Leading
    fig.add_shape(type="rect", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="rgba(241, 196, 15, 0.07)", line_width=0)   # Weakening
    fig.add_shape(type="rect", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="rgba(231, 76, 60, 0.07)", line_width=0)   # Lagging
    fig.add_shape(type="rect", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="rgba(52, 152, 219, 0.07)", line_width=0)   # Improving

    # Draw Crosshair Axis Lines at Center Index Point 100
    fig.add_hline(y=100, line_color="#555555", line_width=2)
    fig.add_vline(x=100, line_color="#555555", line_width=2)

    # Standard clean color hex array to format asset tracks cleanly
    hex_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    unique_assets = master_df['Asset'].unique()
    
    for idx, asset_name in enumerate(unique_assets):
        asset_subset = master_df[master_df['Asset'] == asset_name].sort_values('Sequence')
        color = hex_colors[idx % len(hex_colors)]
        
        # Plot connective history trail line
        fig.add_trace(go.Scatter(
            x=asset_subset['RS_Ratio'], y=asset_subset['RS_Momentum'],
            mode='lines', line=dict(width=3, color=color), hoverinfo='skip', showlegend=False
        ))
        
        # Highlight leading node point
        lead_node = asset_subset.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[lead_node['RS_Ratio']], y=[lead_node['RS_Momentum']],
            mode='markers+text',
            name=asset_name,
            text=[asset_name.split(" ")[0]], # Displays clean primary text title
            textposition="top center",
            marker=dict(size=13, color=color, line=dict(width=2, color="white"))
        ))

    # Static High-Contrast Text Labels anchored inside quadrant regions
    fig.add_annotation(x=max_x-0.8, y=max_y-0.4, text="🟢 LEADING", showarrow=False, font=dict(size=14, color="#17633d"))
    fig.add_annotation(x=max_x-0.8, y=min_y+0.4, text="🟡 WEAKENING", showarrow=False, font=dict(size=14, color="#735c06"))
    fig.add_annotation(x=min_x+0.8, y=min_y+0.4, text="🔴 LAGGING", showarrow=False, font=dict(size=14, color="#7a1515"))
    fig.add_annotation(x=min_x+0.8, y=max_y-0.4, text="🔵 IMPROVING", showarrow=False, font=dict(size=14, color="#12486b"))

    fig.update_layout(
        xaxis=dict(title="JDK RS-Ratio (Trend)", range=[min_x, max_x]),
        yaxis=dict(title="JDK RS-Momentum (Velocity)", range=[min_val if 'min_val' in locals() else min_y, max_y]),
        height=680, margin=dict(l=20, r=20, t=25, b=20),
        legend=dict(orientation="h", y=-0.12)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Core Terminal Output Data Sheet
    st.subheader("📋 Core Terminal Matrix Index")
    latest_matrix = master_df[master_df['Sequence'] == (master_df['Sequence'].max())]
    st.dataframe(latest_matrix[['Asset', 'RS_Ratio', 'RS_Momentum', 'Date']], use_container_width=True, hide_index=True)
