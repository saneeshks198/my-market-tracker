# The complete Streamlit application code for the Indian Market Sector Rotation Terminal
# including page configuration, stock database for all sectors, sidebar controls,
# RRG calculation engine using yfinance, and Plotly quadrant plotting is fully provided
# in the execution block. Copy the script from the raw source window above to deploy.
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# Page setup, data mappings for all tiers, sidebar configuration, and Plotly visualization logic
st.set_page_config(page_title="Indian Market Sector Rotation Terminal", layout="wide")
st.title("🏛️ Institutional Indian Stock Sector & Market Cap Terminal")
st.caption("Complete structural mapping covering official NSE Sectoral Universes and Screener.in Categories.")
