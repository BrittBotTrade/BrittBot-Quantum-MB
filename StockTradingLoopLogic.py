import time
from db_manager import fetch_latest_data, insert_trade_action

# --- Configuration ---
STOCK_ASSET = 'AAPL'
BUY_THRESHOLD = 0.75  # Signal > 0.75 is a strong buy
SELL_THRESHOLD = 0.25 # Signal < 0.25 is a strong sell
TRADE_QUANTITY = 10   # Trade 10 shares per action

def run_stock_engine():
    """
    Runs the stock trading logic based on the latest signal.
    """
    current_time = int(time.time())
    print(f"--- Stock Engine Running at {time.ctime(current_time)} for {STOCK_ASSET} ---")

    # 1. Fetch latest price and signal
    latest_data = fetch_latest_data(STOCK_ASSET, limit=1)
    if not latest_data:
        print(f"   [HOLD] No price data found for {STOCK_ASSET}.")
        return

    latest_price_row = latest_data[0]
    
    # In a real system, you would join or query the signals table specifically
    # For this example, we'll fetch the signal separately
    try:
        from db_manager import get_db_connection
        with get_db_connection() as conn:
            signal_row = conn.execute(
                "SELECT signal_value FROM signals WHERE asset = ? ORDER BY timestamp DESC LIMIT 1",
                (STOCK_ASSET,)
            ).fetchone()
        
        latest_signal = signal_row['signal_value'] if signal_row else 0.5
    except Exception as e:
        print(f"   [ERROR] Could not fetch signal: {e}. Defaulting to HOLD.")
        latest_signal = 0.5
    
    current_price = latest_price_row['price']
    
    # 2. Trading Decision Logic
    action = 'HOLD'
    
    if latest_signal >= BUY_THRESHOLD:
        action = 'BUY'
        
    elif latest_signal <= SELL_THRESHOLD:
        action = 'SELL'
        
    else:
        print(f"   [HOLD] Signal {round(latest_signal, 4)} is neutral (0.25 < x < 0.75).")

    # 3. Execute and Log Trade
    if action in ['BUY', 'SELL']:
        # In a real system, a successful trade confirmation would happen here
        insert_trade_action(
            asset=STOCK_ASSET,
            timestamp=current_time,
            action=action,
            quantity=TRADE_QUANTITY,
            price=current_price
        )
        print(f"   [TRADE EXECUTED] {action} {TRADE_QUANTITY} of {STOCK_ASSET} at ${round(current_price, 2)} (Signal: {round(latest_signal, 4)})")

if __name__ == '__main__':
    # Placeholder test setup (requires data in DB)
    print("Stock Engine test setup is dependent on data and signals being present.")

