"""
Project Chimera: Strategic Intelligence Dashboard (Streamlit App)
"""
import streamlit as st
import pandas as pd
import os

# --- Module Imports ---
# These are the core processing steps of our pipeline
from modules.task_1_collection import run_collection
from modules.task_2_analysis import run_analysis
from modules.task_3_forecasting import run_forecasting
from modules.task_4_dashboard import generate_dashboard_figure

# --- Configuration Loading ---
# Load all settings and API keys from a central config file
try:
    from config import (
        NEWS_API_KEY, GNEWS_API_KEY, TWITTER_BEARER_TOKEN, SLACK_WEBHOOK_URL,
        RAW_NEWS_FILE, ANALYZED_NEWS_FILE, QUERY_TOPIC,
        POSITIVE_THRESHOLD, NEGATIVE_THRESHOLD
    )
except ImportError as e:
    # This block will run if config.py is missing or has an import error
    st.error(f"💥 **Configuration Error:** Could not load settings from `config.py`. Please check the file.")
    st.error(f"Details: {e}")
    st.info("Ensure your `config.py` and `.env` files are correctly set up.")
    st.stop() # Stop the app from running further

# --- App UI ---

st.set_page_config(layout="wide")
st.title("📈 Project Chimera: Strategic Intelligence Dashboard")

# --- Sidebar Controls ---
st.sidebar.header("Dashboard Controls")
query = st.sidebar.text_input("Enter a new topic to analyze:", value=QUERY_TOPIC)
forecast_periods = st.sidebar.selectbox("Select Forecast Period (days):", [7, 15, 30], index=0)

# The main button to trigger the entire analysis pipeline
if st.sidebar.button("🚀 Generate New Report"):
    
    # --- Step 1: Data Collection ---
    with st.spinner("Step 1/4: Collecting articles from NewsAPI, GNews, and Twitter..."):
        collection_success = run_collection(
            query=query, 
            output_filepath=RAW_NEWS_FILE,
            newsapi_key=NEWS_API_KEY,
            gnews_key=GNEWS_API_KEY,
            twitter_token=TWITTER_BEARER_TOKEN
        )

    if not collection_success:
        st.error("Failed to collect any articles. Please check your API keys and the query term.")
        st.stop()
    st.success("Step 1/4: Data collection complete!")

    # --- Step 2: Sentiment Analysis ---
    with st.spinner("Step 2/4: Analyzing sentiment of collected articles..."):
        analysis_success = run_analysis(RAW_NEWS_FILE, ANALYZED_NEWS_FILE)

    if not analysis_success:
        st.error("Sentiment analysis failed. Please check the logs.")
        st.stop()
    st.success("Step 2/4: Sentiment analysis complete!")

    # --- Step 3: Forecasting and Alerting ---
    with st.spinner("Step 3/4: Generating forecast and checking for alerts..."):
        forecast_df = run_forecasting(
            input_filepath=ANALYZED_NEWS_FILE,
            pos_threshold=POSITIVE_THRESHOLD,
            neg_threshold=NEGATIVE_THRESHOLD,
            slack_webhook_url=SLACK_WEBHOOK_URL,
            periods=forecast_periods
        )
    st.success("Step 3/4: Forecasting complete!")

    # --- Step 4: Display Dashboard ---
    with st.spinner("Step 4/4: Creating dashboard visualization..."):
        try:
            analyzed_df = pd.read_csv(ANALYZED_NEWS_FILE)
            analyzed_df['publishedAt'] = pd.to_datetime(analyzed_df['publishedAt'])
            
            fig = generate_dashboard_figure(
                analyzed_df=analyzed_df,
                forecast_df=forecast_df,
                query=query,
                periods=forecast_periods
            )
            st.pyplot(fig)
            st.success("Dashboard generated successfully!")

        except FileNotFoundError:
            st.error(f"Could not find the analyzed data file: {ANALYZED_NEWS_FILE}")
        except Exception as e:
            st.error(f"An error occurred while creating the dashboard: {e}")

else:
    st.info("Enter a topic in the sidebar and click 'Generate New Report' to begin.")
