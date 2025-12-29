import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="FinNews Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 FinNews Market Sentiment Dashboard")

# --- Database Connection ---
# We attempt to locate 'finnews.db'. 
# It is usually created in the working directory where app.py is run.
DB_FILENAME = 'finnews.db'

def get_db_path():
    # Dynamically locate the database relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Check in the same directory (where app.py likely created it)
    local_path = os.path.join(current_dir, DB_FILENAME)
    if os.path.exists(local_path):
        return local_path

    # 2. Fallback: Check in 'storage' subdirectory
    return os.path.join(current_dir, 'storage', DB_FILENAME)

db_path = get_db_path()

@st.cache_data(ttl=60)
def load_data(database_path):
    """Fetches articles and sentiment from the database."""
    if not os.path.exists(database_path):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(database_path)
        # Query assumes tables 'articles' and 'sentiments' exist based on app.py usage
        query = """
            SELECT 
                a.title,
                a.source,
                a.published_at,
                s.label as sentiment,
                a.url
            FROM articles a
            LEFT JOIN sentiments s ON a.id = s.article_id
            ORDER BY a.published_at DESC
            LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error reading database: {e}")
        return pd.DataFrame()

# --- Main UI ---

if not os.path.exists(db_path):
    st.warning(f"⚠️ Database file '{DB_FILENAME}' not found. Please run the main app to collect data first.")
else:
    df = load_data(db_path)

    if df.empty:
        st.info("No data available in the database.")
    else:
        # Layout: 2 columns
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📰 Latest Headlines")
            
            # Display data table
            st.dataframe(
                df[['published_at', 'source', 'title', 'sentiment']],
                column_config={
                    "published_at": "Date",
                    "source": "Source",
                    "title": "Headline",
                    "sentiment": "Sentiment"
                },
                wdith = "stretch",
                hide_index=True
            )

        with col2:
            st.subheader("📊 Market Mood")
            
            if 'sentiment' in df.columns:
                sentiment_counts = df['sentiment'].value_counts()
                
                if not sentiment_counts.empty:
                    # Pie chart using Matplotlib
                    fig, ax = plt.subplots(figsize=(5, 5))
                    colors = {'positive': '#66bb6a', 'negative': '#ef5350', 'neutral': '#bdbdbd'}
                    pie_colors = [colors.get(x, '#cccccc') for x in sentiment_counts.index]
                    
                    ax.pie(
                        sentiment_counts, 
                        labels=sentiment_counts.index, 
                        autopct='%1.1f%%', 
                        startangle=140, 
                        colors=pie_colors,
                        wedgeprops={'edgecolor': 'white'}
                    )
                    st.pyplot(fig)
                    
                    # Metrics
                    total = sentiment_counts.sum()
                    pos = sentiment_counts.get('positive', 0)
                    neg = sentiment_counts.get('negative', 0)
                    
                    st.metric("Total Articles", total)
                    st.metric("Bullish Sentiment", f"{pos/total:.1%}" if total else "0%")

        # Refresh button
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()