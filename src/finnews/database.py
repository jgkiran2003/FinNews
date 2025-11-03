import sqlite3
import os

DB_FILE = os.path.join("data", "processed_articles.db")

def setup_database():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create a simple table to store the URLs of articles we've already seen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_urls (
            url TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def check_if_processed(url):
    """Check if a URL is already in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM processed_urls WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_processed_url(url):
    """Add a new processed URL to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_urls (url) VALUES (?)", (url,))
    conn.commit()
    conn.close()