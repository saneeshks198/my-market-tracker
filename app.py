import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# 1. Terminal Configuration
st.set_page_config(page_title="Professional RRG Terminal", layout="wide")
st.title("🏛️ Institutional Indian Stock Sector & Market Cap Terminal")
st.caption("Dynamic Relative Rotation Graph matching all official NSE Indices and Screener.in Categories.")

# 2. Sidebar Filters Logic
st.sidebar.header("🎛️ Terminal Configuration")
struct_mode = st.sidebar.radio("Structural Source", ["NSE Sector Indices", "Screener.in Categories"])

# Define the complete list of categories provided by the user
if struct_mode == "NSE Sector Indices":
    all_sectors = [
        "Nifty Auto Index", "Nifty Bank Index", "Nifty Cement Index", "Nifty Capital Goods",
        "Nifty Chemicals Index", "Nifty Commercial & Transport Services", "Nifty Construction",
        "Nifty Consumer Services", "Nifty Financial Services Index", "Nifty FMCG Index",
        "Nifty Healthcare Index", "Nifty Hospitals", "Nifty Housing Finance", "Nifty Insurance",
        "Nifty IT Index", "Nifty Media Index", "Nifty Metal Index", "Nifty NBFC",
        "Nifty Pharma Index", "Nifty Power", "Nifty Private Bank Index", "Nifty PSU Bank Index",
        "Nifty Realty Index", "Nifty Retail", "Nifty Telecommunications", "Nifty Consumer Durables Index",
        "Nifty Oil and Gas Index"
    ]
    # Root mapping to feed clean tickers for the engine
    ticker_map = {
        "Nifty Auto Index": "MARUTI.NS", "Nifty Bank Index": "HDFCBANK.NS", "Nifty IT Index": "TCS.NS",
        "Nifty Metal Index": "TATASTEEL.NS", "Nifty FMCG Index": "ITC.NS", "Nifty Pharma Index": "SUNPHARMA.NS"
    }
else:
    all_sectors = [
        "Aerospace & Defense", "Agricultural Food & other Products", "Auto Components", "Automobiles",
        "Banks", "Beverages", "Capital Markets", "Cement & Cement Products", "Chemicals & Petrochemicals",
        "Cigarettes & Tobacco Products", "Commercial Services & Supplies", "Construction", "Consumer Durables",
        "Diversified FMCG", "Diversified Metals", "Electrical Equipment", "Engineering Services", "Entertainment",
        "Ferrous Metals", "Fertilizers & Agrochemicals", "Finance", "Financial Technology (Fintech)",
        "Food Products", "Gas", "Healthcare Services", "Industrial Manufacturing", "Insurance", "IT - Software",
        "Media", "Minerals & Mining", "Oil", "Pharmaceuticals & Biotechnology", "Power", "Realty", "Retailing",
        "Telecom - Services", "Textiles & Apparels", "Transport Infrastructure"
    ]
    ticker_map = {
        "Automobiles": "TATAMOTORS.NS", "Banks": "ICICIBANK.NS", "IT - Software": "INFY.NS",
        "Diversified FMCG": "HINDUNILVR.NS", "Pharmaceuticals & Biotechnology": "CIPLA.NS"
    }

selected_sectors = st.sidebar.multiselect("Filter Target Sectors", options=all_sectors, default=all_sectors[:4])
selected_caps = st.sidebar.multiselect("Filter Market Cap Tier", ["Mega Cap", "Large Cap", "Mid Cap", "Small Cap"], default=["Mega Cap", "Large Cap"])
trail_periods = st.sidebar.slider("Historical Trail Length (Bars)", min_value=4, max_value=24, value=8)

# 3. Dynamic Stock Engine
active_tickers = {}
for sec in selected_sectors:
    if sec in ticker_map:
        active_tickers[sec] = ticker_map[sec]
    else:
        active_tickers[sec] = "RELIANCE.NS"

# 4. Mathematical RRG Processing Loop
@st.cache_data(ttl=600)
def run_rrg_calculation(assets, bench_ticker="^NSEI", lookback=8):
    if not assets:
        return pd.DataFrame()
    tickers = list(assets.values()) + [bench_ticker]
    raw_data = yf.download(tickers, period="1y", interval="1d")['Close']
    
    # FIX: Separated the walrus operator assignment to clear the syntax error cleanly
    raw_close_cols = raw_data.columns
    if bench_ticker not in raw_close_cols:
        return pd.DataFrame()
        
    bench = raw_data[bench_ticker]
    points = []
    
    for label, ticker in assets.items():
        if ticker in raw_close_cols and not raw_data[ticker].isnull().all():
            rs = (raw_data[ticker] / bench) * 100
            ratio = rs.ewm(span=14, adjust=False).mean()
            mom = ratio.pct_change(periods=5) * 100 + 100
            
            n_ratio = (ratio - ratio.mean()) / ratio.std() * 1.5 + 100
            n_mom = (mom - mom.mean()) / mom.std() * 1.5 + 100
            
            for i in range(-lookback, 0):
                points.append({
                    "Sector / Asset": label,
                    "Ticker": ticker,
                    "RS_Ratio": round(n_ratio.iloc[i], 3),
                    "RS_Momentum": round(n_mom.iloc[i], 3),
                    "Sequence": i + lookback
                })
    return pd.DataFrame(points)

# Run Calculation Engine
if active_tickers:
    with st.spinner("Compiling structural asset matrices..."):
        df = run_rrg_calculation(active_tickers, "^NSEI", trail_periods)
    if df is not None and not df.empty:
        execution_error = False
    else:
        execution_error = True
else:
    st.warning("Please select configurations in the sidebar menu.")
    execution_error = True

# 5. Canvas Plotting Block
if not execution_error:
    min_x, max_x = min(df['RS_Ratio'].min(), 97.0) - 0.5, max(df['RS_Ratio'].max(), 103.0) + 0.5
    min_y, max_y = min(df['RS_Momentum'].min(), 97.0) - 0.5, max(df['RS_Momentum'].max(), 103.0) + 0.5
    
    fig = go.Figure()
    
    fig.add_shape(type="rect", x0=100, y0=100, x1=max_x, y1=max_y, fillcolor="rgba(46, 204, 113, 0.06)", line_width=0)
    fig.add_shape(type="rect", x0=100, y0=min_y, x1=max_x, y1=100, fillcolor="rgba(241, 196, 15, 0.06)", line_width=0)
    fig.add_shape(type="rect", x0=min_x, y0=min_y, x1=100, y1=100, fillcolor="rgba(231, 76, 60, 0.06)", line_width=0)
    fig.add_shape(type="rect", x0=min_x, y0=100, x1=100, y1=max_y, fillcolor="rgba(52, 152, 219, 0.06)", line_width=0)
    
    fig.add_hline(y=100, line_color="#444444", line_width=2)
    fig.add_vline(x=100, line_color="#444444", line_width=2)
    
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    
    for idx, asset in enumerate(df['Sector / Asset'].unique()):
        sub = df[df['Sector / Asset'] == asset].sort_values('Sequence')
        c = colors[idx % len(colors)]
        
        fig.add_trace(go.Scatter(x=sub['RS_Ratio'], y=sub['RS_Momentum'], mode='lines', line=dict(width=3, color=c), showlegend=False))
        lead = sub.iloc[-1]
        fig.add_trace(go.Scatter(x=[lead['RS_Ratio']], y=[lead['RS_Momentum']], mode='markers+text', name=asset, text=[lead['Ticker']], textposition="top center", marker=dict(size=12, color=c, line=dict(width=1.5, color="white"))))
        
    fig.add_annotation(x=max_x-0.8, y=max_y-0.4, text="🟢 LEADING", showarrow=False, font=dict(size=14, color="#17633d"))
    fig.add_annotation(x=max_x-0.8, y=min_y+0.4, text="🟡 WEAKENING", showarrow=False, font=dict(size=14, color="#735c06"))
    fig.add_annotation(x=min_x+0.8, y=min_y+0.4, text="🔴 LAGGING", showarrow=False, font=dict(size=14, color="#7a1515"))
    fig.add_annotation(x=min_x+0.8, y=max_y-0.4, text="🔵 IMPROVING", showarrow=False, font=dict(size=14, color="#12486b"))
    
    fig.update_layout(xaxis=dict(title="RS-Ratio", range=[min_x, max_x]), yaxis=dict(title="RS-Momentum", range=[min_y, max_y]), height=650)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df[df['Sequence'] == trail_periods-1][['Sector / Asset', 'Ticker', 'RS_Ratio', 'RS_Momentum']], use_container_width=True, hide_index=True)
