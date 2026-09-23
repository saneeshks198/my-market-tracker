import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# 1. Page Settings
st.set_page_config(page_title="Live Market RRG Tracker", layout="wide")
st.title("📊 Live Market Sector & RRG Tracker")
st.caption("Tracking live trend rotation and market capitalization metrics.")

# 2. Sidebar Filters
st.sidebar.header("🔧 Market Configuration")
market = st.sidebar.selectbox("Select Target Market", ["US Market 🇺🇸", "Indian Market 🇮🇳"])

# Define Live Assets & Benches based on user choice
if market == "US Market 🇺🇸":
    benchmark_ticker = "^GSPC"  # S&P 500 Index
    assets = {
        "Technology (XLK)": "XLK",
        "Financials (XLF)": "XLF",
        "Healthcare (XLV)": "XLV",
        "Energy (XLE)": "XLE",
        "Consumer Discr. (XLY)": "XLY"
    }
else:
    benchmark_ticker = "^NSEI"  # Nifty 50 Index
    assets = {
        "Nifty IT": "NIFTYIT.NS",
        "Nifty Bank": "NIFTYBANK.NS",
        "Nifty Auto": "NIFTYAUTO.NS",
        "Nifty Pharma": "NIFTYPHARMA.NS",
        "Nifty FMCG": "NIFTYFMCG.NS"
    }

# 3. Live Financial Mathematics Engine
@st.cache_data(ttl=600)  # Caches for 10 minutes to avoid hitting rate limits
def fetch_live_rrg_metrics(asset_dict, bench_ticker):
    # Fetch historical data (past 60 days to compute clean indicators)
    all_tickers = list(asset_dict.values()) + [bench_ticker]
    raw_data = yf.download(all_tickers, period="60d", interval="1d")['Close']
    
    rrg_results = []
    bench_series = raw_data[bench_ticker]
    
    for label, ticker in asset_dict.items():
        if ticker in raw_data.columns:
            asset_series = raw_data[ticker]
            
            # Mathematical RRG Foundation:
            # Step A: Relative Strength ratio vs the benchmark index
            rs = (asset_series / bench_series) * 100
            
            # Step B: JDK RS-Ratio (Smoothed Relative Trend using 14-day MA)
            rs_ratio_series = rs.rolling(window=14).mean()
            
            # Step C: JDK RS-Momentum (Rate-of-change velocity of the trend)
            rs_mom_series = rs_ratio_series.pct_change(periods=7) * 100 + 100
            
            # Gather the latest finalized reading
            latest_ratio = rs_ratio_series.iloc[-1]
            latest_momentum = rs_mom_series.iloc[-1]
            
            # Re-index calculations centered precisely at 100 for standard visuals
            adjusted_ratio = 100 + (latest_ratio - rs_ratio_series.mean()) / rs_ratio_series.std() * 2
            adjusted_momentum = 100 + (latest_momentum - rs_mom_series.mean()) / rs_mom_series.std() * 2
            
            rrg_results.append({
                "Asset Name": label,
                "Ticker": ticker,
                "RS_Ratio": round(adjusted_ratio, 2),
                "RS_Momentum": round(adjusted_momentum, 2),
                "Last Price": round(asset_series.iloc[-1], 2)
            })
            
    return pd.DataFrame(rrg_results)

# Run Engine
with st.spinner("Downloading live market historical data streams from Yahoo Finance..."):
    try:
        df_metrics = fetch_live_rrg_metrics(assets, benchmark_ticker)
        data_error = False
    except Exception as e:
        st.error(f"Data pipeline timed out or failed: {e}")
        data_error = True

# 4. Interface Rendering
if not data_error:
    # Render Interactive Plotly RRG Layout
    st.subheader("🔄 Live Relative Rotation Graph")
    
    fig = px.scatter(
        df_metrics, x="RS_Ratio", y="RS_Momentum", text="Asset Name", color="Asset Name",
        range_x=[94, 106], range_y=[94, 106],
        labels={"RS_Ratio": "JDK RS-Ratio (Trend Strength)", "RS_Momentum": "JDK RS-Momentum (Velocity)"}
    )
    
    # Overlay static quadrants crosshairs 
    fig.add_hline(y=100, line_dash="dash", line_color="black", line_width=1.5)
    fig.add_vline(x=100, line_dash="dash", line_color="black", line_width=1.5)
    
    # Text anchors for quadrant definitions
    fig.add_annotation(x=104, y=105, text="🟢 LEADING", showarrow=False, font=dict(color="green", size=15, weight="bold"))
    fig.add_annotation(x=104, y=95, text="🟡 WEAKENING", showarrow=False, font=dict(color="orange", size=15, weight="bold"))
    fig.add_annotation(x=96, y=95, text="🔴 LAGGING", showarrow=False, font=dict(color="red", size=15, weight="bold"))
    fig.add_annotation(x=96, y=105, text="🔵 IMPROVING", showarrow=False, font=dict(color="blue", size=15, weight="bold"))
    
    fig.update_traces(marker=dict(size=16), textposition='top center')
    st.plotly_chart(fig, use_container_width=True)
    
    # Render Live Data Metrics Sheet
    st.subheader("📋 Sector Pricing & Metric Index Summary")
    st.dataframe(df_metrics, use_container_width=True, hide_index=True)
