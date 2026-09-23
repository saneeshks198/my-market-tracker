import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# 1. Page Configuration (Terminal Theme)
st.set_page_config(page_title="Professional RRG Terminal", layout="wide")
st.title("🏛️ Institutional Relative Rotation Graph Terminal")
st.caption("De Kempenaer Rotation Model with true multi-period vector paths and canvas quadrant shading.")

# 2. Controls & Sidebar Setup
st.sidebar.header("🎛️ Terminal Configuration")
market = st.sidebar.selectbox("Market Universe", ["US Market 🇺🇸", "Indian Market 🇮🇳"])
interval = st.sidebar.selectbox("Data Interval (Weekly Recommended)", ["1wk", "1d"])
trail_periods = st.sidebar.slider("Historical Trail Length (Bars)", min_value=4, max_value=24, value=8)

if market == "US Market 🇺🇸":
    benchmark = "^GSPC"  # S&P 500 Index
    universe = {
        "Technology (XLK)": "XLK", "Financials (XLF)": "XLF", 
        "Healthcare (XLV)": "XLV", "Energy (XLE)": "XLE", 
        "Consumer Discretionary (XLY)": "XLY", "Industrials (XLI)": "XLI"
    }
else:
    benchmark = "^NSEI"  # Nifty 50 Index
    universe = {
        "Nifty IT": "NIFTYIT.NS", "Nifty Bank": "NIFTYBANK.NS", 
        "Nifty Auto": "NIFTYAUTO.NS", "Nifty Pharma": "NIFTYPHARMA.NS", 
        "Nifty FMCG": "NIFTYFMCG.NS", "Nifty Infra": "NIFTYINFRA.NS"
    }

# 3. Mathematical RRG Engine
@st.cache_data(ttl=600)
def compute_true_rrg(assets_dict, bench_ticker, data_interval):
    tickers_list = list(assets_dict.values()) + [bench_ticker]
    raw_close = yf.download(tickers_list, period="1y", interval=data_interval)['Close']
    
    bench_series = raw_close[bench_ticker]
    all_points = []
    
    df_rs = pd.DataFrame({label: (raw_close[ticker] / bench_series) * 100 
                          for label, ticker in assets_dict.items() if ticker in raw_close.columns})
    
    rs_ratio_raw = df_rs.ewm(span=14, adjust=False).mean()
    rs_momentum_raw = rs_ratio_raw.pct_change(periods=5) * 100 + 100
    
    normalized_ratio = (rs_ratio_raw - rs_ratio_raw.mean()) / rs_ratio_raw.std() * 1.5 + 100
    normalized_momentum = (rs_momentum_raw - rs_momentum_raw.mean()) / rs_momentum_raw.std() * 1.5 + 100
    
    for label in assets_dict.keys():
        for i in range(-trail_periods, 0):
            date_str = normalized_ratio.index[i].strftime('%Y-%m-%d')
            all_points.append({
                "Asset": label,
                "Date": date_str,
                "RS_Ratio": round(normalized_ratio[label].iloc[i], 3),
                "RS_Momentum": round(normalized_momentum[label].iloc[i], 3),
                "Sequence": i + trail_periods
            })
            
    return pd.DataFrame(all_points)

# Run Calculations
with st.spinner("Compiling institutional asset matrices..."):
    try:
        master_df = compute_true_rrg(universe, benchmark, interval)
        execution_error = False
    except Exception as e:
        st.error(f"Engine matrix failure: {e}")
        execution_error = True

# 4. Canvas Rendering Block
if not execution_error:
    min_val, max_val = 96.5, 103.5
    fig = go.Figure()

    # Add Translucent Colored Background Rectangles to define true Quadrants
    fig.add_shape(type="rect", x0=100, y0=100, x1=max_val, y1=max_val, fillcolor="rgba(46, 204, 113, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=min_val, x1=max_val, y1=100, fillcolor="rgba(241, 196, 15, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=min_val, y0=min_val, x1=100, y1=100, fillcolor="rgba(231, 76, 60, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=min_val, y0=100, x1=100, y1=max_val, fillcolor="rgba(52, 152, 219, 0.08)", line_width=0)

    # Draw the Quadrant Separator Grid Lines
    fig.add_hline(y=100, line_color="#444444", line_width=2)
    fig.add_vline(x=100, line_color="#444444", line_width=2)

    # Hardcoded clean color hex palette to avoid any missing module errors
    hex_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    
    for idx, asset_name in enumerate(universe.keys()):
        asset_subset = master_df[master_df['Asset'] == asset_name].sort_values('Sequence')
        color = hex_colors[idx % len(hex_colors)]
        
        # Plot full connecting history line (The Tail)
        fig.add_trace(go.Scatter(
            x=asset_subset['RS_Ratio'], y=asset_subset['RS_Momentum'],
            mode='lines', line=dict(width=3, color=color), hoverinfo='skip', showlegend=False
        ))
        
        # Plot the final lead node using a standard stable circle marker
        lead_node = asset_subset.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[lead_node['RS_Ratio']], y=[lead_node['RS_Momentum']],
            mode='markers+text',
            name=asset_name,
            text=[asset_name], 
            textposition="top center",
            marker=dict(size=14, color=color, line=dict(width=2, color="white"))
        ))

    # Absolute High-Contrast Anchor Text Placements
    fig.add_annotation(x=max_val-0.5, y=max_val-0.4, text="🟢 LEADING", showarrow=False, font=dict(size=14, color="#17633d"))
    fig.add_annotation(x=max_val-0.5, y=min_val+0.4, text="🟡 WEAKENING", showarrow=False, font=dict(size=14, color="#735c06"))
    fig.add_annotation(x=min_val+0.5, y=min_val+0.4, text="🔴 LAGGING", showarrow=False, font=dict(size=14, color="#7a1515"))
    fig.add_annotation(x=min_val+0.5, y=max_val-0.4, text="🔵 IMPROVING", showarrow=False, font=dict(size=14, color="#12486b"))

    # Layout Customizations
    fig.update_layout(
        xaxis=dict(title="JDK RS-Ratio (Trend Strength)", range=[min_val, max_val]),
        yaxis=dict(title="JDK RS-Momentum (Velocity Component)", range=[min_val, max_val]),
        height=650, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", y=-0.15)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Core Terminal Output Data Sheet
    st.subheader("📋 Core Terminal Matrix Index")
    latest_matrix = master_df[master_df['Sequence'] == (trail_periods - 1)]
    st.dataframe(latest_matrix[['Asset', 'RS_Ratio', 'RS_Momentum']], use_container_width=True, hide_index=True)

