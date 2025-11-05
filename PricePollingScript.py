import time
import requests
import random
from db_manager import insert_price_data

# --- Configuration ---
# In a real system, you would use API keys and secure endpoints here.
STOCKS = ['AAPL']
CRYPTOS = ['BTC']
MOCK_PRICES = {'AAPL': 170.00, 'BTC': 65000.00}

def fetch_and_store_data():
    """
    Simulates polling price data from external APIs and stores it in the DB.
    """
    current_time = int(time.time())
    print(f"--- Data Feeder Running at {time.ctime(current_time)} ---")

    assets = STOCKS + CRYPTOS
    
    for asset in assets:
        try:
            # --- REAL API CALL SIMULATION ---
            # In a live system, this would be a network call:
            # response = requests.get(f"https://api.exchange.com/v1/ticker/{asset}")
            # current_price = response.json()['price']

            # --- MOCK DATA GENERATION (for demonstration) ---
            # Simulate a small random walk to keep the price dynamic
            mock_price = MOCK_PRICES[asset]
            fluctuation = random.uniform(-0.005, 0.005) * mock_price # +/- 0.5%
            current_price = mock_price + fluctuation
            MOCK_PRICES[asset] = current_price # Update mock for next run

            # Store the data
            insert_price_data(asset, current_time, round(current_price, 4))
            print(f"   [SUCCESS] {asset}: {round(current_price, 2)}")

        except Exception as e:
            print(f"   [ERROR] Failed to fetch data for {asset}: {e}")

if __name__ == '__main__':
    # Test the data feeder
    fetch_and_store_data()

