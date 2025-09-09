import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Set page config
st.set_page_config(
    page_title="NIFTY 50 INDIA Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("📊 Nifty 50 Stock Analysis")
st.markdown("""
This app analyzes price patterns for Nifty 50 stocks since 2008.
It calculates the percentage of days where different price conditions occurred.
""")

# Sidebar for user inputs
with st.sidebar:
    st.header("Settings")
    start_date = st.date_input("Start Date", value=pd.to_datetime("2008-01-01"))
    show_progress = st.checkbox("Show Progress Updates", value=True)
    auto_refresh = st.checkbox("Auto-refresh Data", value=False)
    
    if auto_refresh:
        refresh_interval = st.slider("Refresh Interval (minutes)", 1, 60, 15)
        if st.button("Refresh Now"):
            st.cache_data.clear()

# Nifty 50 companies
nifty_50 = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS",
    "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS", "PFC.NS"
]

@st.cache_data(ttl=3600 if auto_refresh else 86400)  # Cache for 1 hour or 1 day
def get_stock_data(ticker, start_date):
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        return data
    except Exception as e:
        st.error(f"Error downloading {ticker}: {str(e)}")
        return None

def calculate_metrics(data, ticker):
    if data is None or len(data) == 0:
        return None

    try:
        # Calculate price differences
        diff_high_open = data["High"] - data["Open"]
        diff_open_low = data["Open"] - data["Low"]

        # Calculate price equality percentages
        price_equality = {
            'High=Open%': (diff_high_open == 0).mean() * 100,
            'High>Open%': (diff_high_open > 0).mean() * 100,
            'High>Open>Low%': ((diff_high_open > 0) & (diff_open_low > 0)).mean() * 100,
            'High=Open>Low%': ((diff_high_open == 0) & (diff_open_low > 0)).mean() * 100,
            'Low=Open%': (diff_open_low == 0).mean() * 100,
            'Low<Open%': (diff_open_low > 0).mean() * 100
        }

        # Create metrics dictionary
        metrics = {
            'Ticker': ticker.replace(".NS", ""),
        }

        # Add price equality metrics
        for k, v in price_equality.items():
            metrics[k] = float(v)

        return metrics

    except Exception as e:
        st.error(f"Error calculating metrics for {ticker}: {str(e)}")
        return None

# Main analysis function
def run_analysis():
    st.info("Starting Comprehensive Stock Analysis...")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(nifty_50):
        if show_progress:
            status_text.text(f"Processing: {ticker.replace('.NS', '')} ({i+1}/{len(nifty_50)})")
            progress_bar.progress((i + 1) / len(nifty_50))
        
        data = get_stock_data(ticker, start_date)
        metrics = calculate_metrics(data, ticker)
        if metrics:
            results.append(metrics)
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    return results

# Run the analysis
if st.button("Run Analysis", type="primary") or auto_refresh:
    results = run_analysis()
    
    if not results:
        st.error("All stock processing failed. Please check your internet connection.")
    else:
        # Create DataFrame
        df = pd.DataFrame(results)

        # Add Buy/Sell signal based on comparison
        df['Signal'] = df.apply(lambda row: 'BUY' if row['High>Open%'] > row['Low<Open%'] else 'SELL', axis=1)

        # Sort and format output
        final_results = df.sort_values('High>Open>Low%', ascending=False)
        
        # Display results
        st.success(f"Analysis complete! Processed {len(results)} stocks.")
        
        # Metrics explanation
        with st.expander("📖 Metrics Explanation"):
            st.markdown("""
            - **High>Open>Low%**: Days where High > Open > Low
            - **High=Open>Low%**: Days where High = Open > Low  
            - **Low<Open%**: Days where Low < Open
            - **Low=Open%**: Days where Low = Open
            - **High>Open%**: Days where High > Open
            - **High=Open%**: Days where High = Open
            - **Signal**: BUY if High>Open% > Low<Open%, else SELL
            """)
        
        # Display data table
        st.subheader("Analysis Results")
        
        # Format the display
        display_df = final_results[['Ticker', 'High>Open>Low%', 'High=Open>Low%',
                                    'Low<Open%', 'Low=Open%', 'High>Open%', 'High=Open%',
                                    'Signal']].copy()
        
        # Format percentages
        for col in display_df.columns:
            if '%' in col:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
        
        # Show the table
        st.dataframe(display_df, use_container_width=True, height=600)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("BUY Signals", f"{len(display_df[display_df['Signal'] == 'BUY'])}")
        with col2:
            st.metric("SELL Signals", f"{len(display_df[display_df['Signal'] == 'SELL'])}")
        with col3:
            avg_buy = final_results[final_results['Signal'] == 'BUY']['High>Open>Low%'].mean()
            st.metric("Avg BUY Score", f"{avg_buy:.2f}%")
        with col4:
            avg_sell = final_results[final_results['Signal'] == 'SELL']['High>Open>Low%'].mean()
            st.metric("Avg SELL Score", f"{avg_sell:.2f}%")
        
        # Download button
        csv = final_results.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name=f"nifty_50_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.caption(f"Data from Yahoo Finance | Analysis from {start_date} to {datetime.now().strftime('%Y-%m-%d')}")

# Auto-refresh logic
if auto_refresh:
    st.write(f"Auto-refresh enabled: will refresh every {refresh_interval} minutes")
    time.sleep(refresh_interval * 60)

    st.experimental_rerun()

