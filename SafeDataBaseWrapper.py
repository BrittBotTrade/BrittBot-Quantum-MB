import sqlite3
from contextlib import contextmanager
import time

# --- Configuration ---
DATABASE_FILE = 'trading_data.db'

@contextmanager
def get_db_connection():
    """
    Context manager for safe database connection and transaction handling.
    Ensures connection is closed and committed/rolled back.
    """
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def initialize_database():
    """
    Initializes the database structure with necessary tables.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Price Data Table (Time-series)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                price REAL NOT NULL,
                UNIQUE(asset, timestamp)
            );
        """)

        # 2. Trading Signals Table (AI/Brain output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                signal_value REAL NOT NULL, -- e.g., 0.5 for neutral, 1.0 for strong buy
                sma_20 REAL,
                sma_50 REAL
            );
        """)

        # 3. Trade History/Actions Table (Engine output)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                action TEXT NOT NULL, -- BUY, SELL, HOLD
                quantity REAL,
                price REAL
            );
        """)

        print(f"Database initialized: {DATABASE_FILE}")

def fetch_latest_data(asset, limit=100):
    """
    Fetches the latest price data for a given asset.
    Returns a list of dictionaries (sqlite3.Row objects).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM price_data WHERE asset = ? ORDER BY timestamp DESC LIMIT ?",
            (asset, limit)
        )
        return cursor.fetchall()

def insert_price_data(asset, timestamp, price):
    """Inserts or updates a single price data point."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO price_data (asset, timestamp, price) VALUES (?, ?, ?)",
                (asset, timestamp, price)
            )
    except Exception as e:
        print(f"Error inserting price data: {e}")

def insert_signal(asset, timestamp, signal_value, sma_20, sma_50):
    """Inserts a new trading signal."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO signals (asset, timestamp, signal_value, sma_20, sma_50) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (asset, timestamp, signal_value, sma_20, sma_50)
            )
    except Exception as e:
        print(f"Error inserting signal: {e}")

def insert_trade_action(asset, timestamp, action, quantity, price):
    """Inserts a trade action into the history."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO trade_history (asset, timestamp, action, quantity, price) VALUES (?, ?, ?, ?, ?)",
                (asset, timestamp, action, quantity, price)
            )
    except Exception as e:
        print(f"Error inserting trade action: {e}")

def get_dashboard_summary():
    """Fetches high-level data for the Flask dashboard."""
    summary = {}
    ASSETS = ['AAPL', 'BTC']
    with get_db_connection() as conn:
        for asset in ASSETS:
            # Latest Price
            latest_price = conn.execute(
                "SELECT price, timestamp FROM price_data WHERE asset = ? ORDER BY timestamp DESC LIMIT 1",
                (asset,)
            ).fetchone()

            # Latest Signal
            latest_signal = conn.execute(
                "SELECT signal_value, sma_20, sma_50 FROM signals WHERE asset = ? ORDER BY timestamp DESC LIMIT 1",
                (asset,)
            ).fetchone()

            # Last 5 Trades
            trades = conn.execute(
                "SELECT timestamp, action, quantity, price FROM trade_history WHERE asset = ? ORDER BY timestamp DESC LIMIT 5",
                (asset,)
            ).fetchall()

            summary[asset] = {
                'price': latest_price['price'] if latest_price else 0.0,
                'timestamp': latest_price['timestamp'] if latest_price else 0,
                'signal': latest_signal['signal_value'] if latest_signal else 0.5,
                'sma_20': latest_signal['sma_20'] if latest_signal else 0.0,
                'sma_50': latest_signal['sma_50'] if latest_signal else 0.0,
                'trades': [dict(t) for t in trades]
            }
    return summary

if __name__ == '__main__':
    # Simple test for database functionality
    initialize_database()
    print("DB Manager test complete.")

