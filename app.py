
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Market Tracker", layout="wide")
st.title("📊 Personal Market & RRG Tracker")

# 2. Sidebar Filters
st.sidebar.header("Settings")
market = st.sidebar.selectbox("Market", ["US Market 🇺🇸", "Indian Market 🇮🇳"])
cap_filter = st.sidebar.multiselect("Market Cap", ["Mega", "Large", "Mid"], default=["Mega", "Large"])

# 3. Create Sample Data to verify layout works instantly
sectors = ["Technology", "Financials", "Healthcare", "Energy", "Consumer"] if market == "US Market 🇺🇸" else ["IT", "Banking", "Auto", "Pharma", "FMCG"]
df = pd.DataFrame({
    "Sector": sectors,
    "RS_Ratio": np.random.uniform(96, 104, len(sectors)),
    "RS_Momentum": np.random.uniform(96, 104, len(sectors))
})

# 4. Draw RRG Chart
st.subheader("🔄 Relative Rotation Graph")
fig = px.scatter(df, x="RS_Ratio", y="RS_Momentum", text="Sector", color="Sector", range_x=[95, 105], range_y=[95, 105])
fig.add_hline(y=100, line_dash="dash", line_color="gray")
fig.add_vline(x=100, line_dash="dash", line_color="gray")
st.plotly_chart(fig, use_container_width=True)

# 5. Stock Watchlist
st.subheader("📋 Sector Components")
st.write(df)
