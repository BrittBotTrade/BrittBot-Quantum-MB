import pandas as pd
import numpy as np
import time
from db_manager import fetch_latest_data, insert_signal

# --- Configuration ---
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50

def generate_signals(asset):
    """
    Calculates trading signals for a given asset using a simple SMA Crossover strategy.
    
    Signal Logic:
    - If SMA_SHORT > SMA_LONG, signal_value > 0.5 (Buy)
    - If SMA_SHORT < SMA_LONG, signal_value < 0.5 (Sell/Hold)
    - The further apart they are, the stronger the signal (closer to 1.0 or 0.0).
    """
    data = fetch_latest_data(asset, limit=SMA_LONG_PERIOD + 5)
    
    if len(data) < SMA_LONG_PERIOD:
        print(f"[SKIP] Not enough data for {asset}. Need {SMA_LONG_PERIOD}, found {len(data)}.")
        return

    # Convert SQLite rows to a pandas DataFrame
    df = pd.DataFrame(data)
    df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
    
    # Calculate Simple Moving Averages (SMA)
    df['SMA_20'] = df['price'].rolling(window=SMA_SHORT_PERIOD).mean()
    df['SMA_50'] = df['price'].rolling(window=SMA_LONG_PERIOD).mean()

    # Get the latest calculated values
    latest = df.iloc[-1]
    
    sma_20 = latest['SMA_20']
    sma_50 = latest['SMA_50']
    
    # --- Generate Signal Value ---
    if pd.isna(sma_20) or pd.isna(sma_50):
        # Default to neutral if SMAs are not yet calculated (due to not enough data)
        signal_value = 0.5
    else:
        # Calculate the difference relative to the price for normalization
        price = latest['price']
        diff_pct = (sma_20 - sma_50) / price # Difference as a percentage of price
        
        # Scale the signal: map a reasonable range of diff_pct (e.g., -0.05 to +0.05) to 0 to 1
        # 0.05 is 5% difference, which is a strong move
        
        # Normalize diff_pct to a -1.0 to 1.0 range based on a max expected difference (0.05)
        max_diff = 0.01 # Max expected difference in 1% of price
        normalized_diff = np.clip(diff_pct / max_diff, -1.0, 1.0)
        
        # Shift and scale to 0.0 to 1.0 range
        # -1.0 -> 0.0 (Strong Sell)
        # 0.0 -> 0.5 (Neutral)
        # 1.0 -> 1.0 (Strong Buy)
        signal_value = (normalized_diff + 1.0) / 2.0
    
    # Store the signal in the database
    insert_signal(
        asset=asset,
        timestamp=int(time.time()),
        signal_value=round(signal_value, 4),
        sma_20=round(sma_20, 4) if not pd.isna(sma_20) else None,
        sma_50=round(sma_50, 4) if not pd.isna(sma_50) else None
    )
    
    print(f"   [SIGNAL] {asset}: Signal={round(signal_value, 4)}, SMA20={round(sma_20, 2) if not pd.isna(sma_20) else 'N/A'}")

def update_brain():
    """Main function to run the AI/Math calculations for all assets."""
    print("--- Brain Update Running ---")
    
    # In a full system, this list would be dynamic
    ASSETS_TO_ANALYZE = ['AAPL', 'BTC']
    
    for asset in ASSETS_TO_ANALYZE:
        generate_signals(asset)

if __name__ == '__main__':
    # Placeholder test setup (requires data in DB)
    print("Brain Update test setup is dependent on data being present.")

