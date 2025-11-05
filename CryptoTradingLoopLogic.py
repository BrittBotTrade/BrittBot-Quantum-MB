import time
from db_manager import fetch_latest_data, insert_trade_action

# --- Configuration ---
CRYPTO_ASSET = 'BTC'
BUY_THRESHOLD = 0.80  # Higher threshold due to higher volatility
SELL_THRESHOLD = 0.20 # Lower threshold due to higher volatility
TRADE_QUANTITY = 0.01 # Trade 0.01 BTC per action

def run_crypto_engine():
    """
    Runs the crypto trading logic based on the latest signal.
    """
    current_time = int(time.time())
    print(f"--- Crypto Engine Running at {time.ctime(current_time)} for {CRYPTO_ASSET} ---")

    # 1. Fetch latest price and signal
    latest_data = fetch_latest_data(CRYPTO_ASSET, limit=1)
    if not latest_data:
        print(f"   [HOLD] No price data found for {CRYPTO_ASSET}.")
        return

    latest_price_row = latest_data[0]
    
    # Fetch the signal (copied logic from stock_engine for self-contained example)
    try:
        from db_manager import get_db_connection
        with get_db_connection() as conn:
            signal_row = conn.execute(
                "SELECT signal_value FROM signals WHERE asset = ? ORDER BY timestamp DESC LIMIT 1",
                (CRYPTO_ASSET,)
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
        print(f"   [HOLD] Signal {round(latest_signal, 4)} is neutral (0.20 < x < 0.80).")

    # 3. Execute and Log Trade
    if action in ['BUY', 'SELL']:
        # In a real system, a successful trade confirmation would happen here
        insert_trade_action(
            asset=CRYPTO_ASSET,
            timestamp=current_time,
            action=action,
            quantity=TRADE_QUANTITY,
            price=current_price
        )
        print(f"   [TRADE EXECUTED] {action} {TRADE_QUANTITY} of {CRYPTO_ASSET} at ${round(current_price, 2)} (Signal: {round(latest_signal, 4)})")

if __name__ == '__main__':
    # Placeholder test setup (requires data in DB)
    print("Crypto Engine test setup is dependent on data and signals being present.")

