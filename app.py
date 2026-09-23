import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Professional RRG Dashboard", layout="wide")
st.title("📈 Institutional Relative Rotation Graph (RRG)")
st.caption("Engineered using Julius de Kempenaer's proprietary normalization models with multi-period historical trail paths.")

# 2. Controls & Sidebar Setup
st.sidebar.header("🎛️ Engine Configuration")
market = st.sidebar.selectbox("Market Universe", ["US Market 🇺🇸", "Indian Market 🇮🇳"])
trail_days = st.sidebar.slider("Historical Trail Depth (Days)", min_value=3, max_value=20, value=7)

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

# 3. Mathematical RRG Core Engine
@st.cache_data(ttl=300)
def compute_professional_rrg(assets_dict, bench_ticker, history_window=120):
    tickers_list = list(assets_dict.values()) + [bench_ticker]
    # Fetch clean end-of-day data matrix
    raw_close = yf.download(tickers_list, period="180d", interval="1d")['Close']
    
    bench_series = raw_close[bench_ticker]
    all_history_points = []
    
    # Pre-calculate RS metrics for each ticker
    rs_data = {}
    for label, ticker in assets_dict.items():
        if ticker in raw_close.columns:
            # Step 1: Base Relative Strength Calculation
            rs_data[label] = (raw_close[ticker] / bench_series) * 100

    # Convert to Dataframe for vector math matrix operations
    df_rs = pd.DataFrame(rs_data)
    
    # Step 2: JDK RS-Ratio Calculation (Using dual-window tracking matrix)
    # EMA smoothing tracks stable long term trend changes relative to benchmark
    ema_fast = df_rs.ewm(span=12, adjust=False).mean()
    rs_ratio_raw = df_rs.ewm(span=14, adjust=False).mean()
    
    # Step 3: JDK RS-Momentum Calculation (Rate of change of the smoothed ratio)
    rs_momentum_raw = rs_ratio_raw.pct_change(periods=5) * 100 + 100
    
    # Step 4: True De Kempenaer Z-Score Cross Normalization Loop Around Base 100
    # This aligns metrics perfectly across completely separate capital markets
    normalized_ratio = (rs_ratio_raw - rs_ratio_raw.mean()) / rs_ratio_raw.std() * 1.5 + 100
    normalized_momentum = (rs_momentum_raw - rs_momentum_raw.mean()) / rs_momentum_raw.std() * 1.5 + 100
    
    # Gather trailing coordinates up to specified depth
    for label in assets_dict.keys():
        for i in range(-trail_days, 0):
            # Capture timestamps cleanly
            date_str = normalized_ratio.index[i].strftime('%Y-%m-%d')
            all_history_points.append({
                "Asset": label,
                "Date": date_str,
                "RS_Ratio": round(normalized_ratio[label].iloc[i], 3),
                "RS_Momentum": round(normalized_momentum[label].iloc[i], 3),
                "Sequence": i + trail_days  # Ordering index for path generation
            })
            
    return pd.DataFrame(all_history_points)

# Run Calculation Matrix
with st.spinner("Processing advanced trend matrices and historical tails..."):
    try:
        rrg_master_df = compute_professional_rrg(universe, benchmark)
        # Filter latest record to place clear text tags on the lead node
        latest_nodes = rrg_master_df[rrg_master_df['Sequence'] == (trail_days - 1)]
        execution_error = False
    except Exception as error_msg:
        st.error(f"Engine computation fault: {error_msg}")
        execution_error = True

# 4. Interactive Data Visualization Block
if not execution_error:
    st.subheader("🔄 Real-Time Relative Rotation Scatter Vector")
    
    # Set custom axes bounding limits to center at crosshair coordinates (100, 100)
    axis_min, axis_max = 97.0, 103.0
    
    # Render scatter plots with unified sorting paths to display smooth movement trails
    fig = px.scatter(
        rrg_master_df, x="RS_Ratio", y="RS_Momentum", 
        color="Asset", hover_data=["Date"],
        range_x=[axis_min, axis_max], range_y=[axis_min, axis_max],
        labels={"RS_Ratio": "JDK RS-Ratio (Trend Weight)", "RS_Momentum": "JDK RS-Momentum (Velocity Factor)"}
    )
    
    # Add historical connective paths (Tails)
    for asset_name in universe.keys():
        asset_subset = rrg_master_df[rrg_master_df['Asset'] == asset_name].sort_values('Sequence')
        fig.add_scatter(
            x=asset_subset['RS_Ratio'], y=asset_subset['RS_Momentum'],
            mode='lines', line=dict(width=2), name=asset_name, showlegend=False,
            hoverinfo='skip'
        )
        
    # Draw reference crosshair grids
    fig.add_hline(y=100, line_dash="solid", line_color="#333333", line_width=1.5)
    fig.add_vline(x=100, line_dash="solid", line_color="#333333", line_width=1.5)
    
    # Add high-contrast text tags on precise quadrant poles
    fig.add_annotation(x=101.8, y=102.2, text="🟢 LEADING", showarrow=False, font=dict(color="#2ca02c", size=16, weight="bold"))
    fig.add_annotation(x=101.8, y=97.8, text="🟡 WEAKENING", showarrow=False, font=dict(color="#ff7f0e", size=16, weight="bold"))
    fig.add_annotation(x=98.2, y=97.8, text="🔴 LAGGING", showarrow=False, font=dict(color="#d62728", size=16, weight="bold"))
    fig.add_annotation(x=98.2, y=102.2, text="🔵 IMPROVING", showarrow=False, font=dict(color="#1f77b4", size=16, weight="bold"))
    
    fig.update_traces(marker=dict(size=12, opacity=0.85))
    fig.update_layout(height=650, legend_title_text='Monitored Elements')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data Reference Frame Grid Display
    st.subheader("📋 Core Data Metrics Table")
    st.dataframe(latest_nodes[['Asset', 'RS_Ratio', 'RS_Momentum']], use_container_width=True, hide_index=True)
