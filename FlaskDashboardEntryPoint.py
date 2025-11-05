from flask import Flask, render_template_string
import time
from apscheduler.schedulers.background import BackgroundScheduler
from db_manager import initialize_database, get_dashboard_summary
from data_feeder import fetch_and_store_data
from brain_update import update_brain
from stock_engine import run_stock_engine
from crypto_engine import run_crypto_engine

# --- Flask App Initialization ---
app = Flask(__name__)

# --- APScheduler Setup ---
scheduler = BackgroundScheduler()

def start_scheduled_jobs():
    """Initializes and starts the background jobs."""
    print("Scheduler: Starting background trading system jobs.")
    
    # 1. Data Feeder: Poll prices every 5 seconds (fastest job)
    scheduler.add_job(fetch_and_store_data, 'interval', seconds=5, id='data_feeder')

    # 2. Brain Update: Calculate signals every 10 seconds (needs fresh data)
    scheduler.add_job(update_brain, 'interval', seconds=10, id='brain_update')

    # 3. Trading Engines: Run trade logic every 30 seconds
    scheduler.add_job(run_stock_engine, 'interval', seconds=30, id='stock_engine')
    scheduler.add_job(run_crypto_engine, 'interval', seconds=30, id='crypto_engine')
    
    # Start the scheduler
    scheduler.start()
    print("Scheduler: All jobs scheduled and running.")

# --- Database Initialization and Scheduler Startup ---
with app.app_context():
    initialize_database()
    start_scheduled_jobs()

# --- Jinja2 Template for Dashboard (In-line for single-file submission) ---
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Trading Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f4f7f9; }
        .card { background-color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .signal-buy { background-color: #10b981; color: white; }
        .signal-sell { background-color: #ef4444; color: white; }
        .signal-hold { background-color: #fbbf24; color: #333; }
        .text-timestamp { font-size: 0.75rem; color: #6b7280; }
        .trade-buy { color: #10b981; font-weight: bold; }
        .trade-sell { color: #ef4444; font-weight: bold; }
    </style>
</head>
<body class="p-4 sm:p-8">
    <div class="max-w-7xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-800 mb-6 border-b pb-2">Autonomous Trading Dashboard</h1>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for asset, data in summary.items() %}
            <div class="card p-5">
                <h2 class="text-2xl font-semibold mb-4 flex justify-between items-center">
                    {{ asset }}
                    {% set signal_class = 'signal-buy' if data.signal >= 0.75 else ('signal-sell' if data.signal <= 0.25 else 'signal-hold') %}
                    <span class="px-3 py-1 text-sm rounded-full {{ signal_class }}">
                        Signal: {{ data.signal | round(4) }}
                    </span>
                </h2>

                <div class="space-y-2 mb-4">
                    <p class="text-xl font-mono text-gray-700">Current Price: <span class="font-bold text-2xl">${{ data.price | round(4) }}</span></p>
                    <p class="text-timestamp">Last Updated: {{ data.timestamp | format_timestamp }}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-2 text-sm mb-4 p-3 bg-gray-50 rounded-lg">
                    <p class="font-medium text-gray-600">SMA 20:</p>
                    <p class="font-bold text-right">${{ data.sma_20 | round(2) if data.sma_20 is not none else 'N/A' }}</p>
                    <p class="font-medium text-gray-600">SMA 50:</p>
                    <p class="font-bold text-right">${{ data.sma_50 | round(2) if data.sma_50 is not none else 'N/A' }}</p>
                </div>

                <h3 class="text-lg font-medium text-gray-700 mb-3 border-t pt-4">Trade History (Latest)</h3>
                <ul class="space-y-2">
                    {% for trade in data.trades %}
                    <li class="flex justify-between text-sm py-1 border-b last:border-b-0">
                        <span class="font-mono {{ 'trade-buy' if trade.action == 'BUY' else ('trade-sell' if trade.action == 'SELL' else 'text-gray-500') }}">
                            {{ trade.action }}
                        </span>
                        <span class="text-gray-600">{{ trade.quantity | round(4) }} @ ${{ trade.price | round(4) }}</span>
                        <span class="text-timestamp">{{ trade.timestamp | format_timestamp }}</span>
                    </li>
                    {% else %}
                    <li class="text-center text-gray-500">No recent trades recorded.</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </div>
        
        <footer class="mt-8 text-center text-sm text-gray-500">
            <p>Trading System Status: Operational</p>
        </footer>
    </div>
</body>
</html>
"""

# --- Custom Jinja Filter ---
def format_timestamp(timestamp):
    """Converts Unix timestamp to readable time string."""
    if timestamp:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
    return "N/A"

app.jinja_env.filters['format_timestamp'] = format_timestamp

# --- Flask Routes ---
@app.route('/')
def dashboard():
    """Renders the main trading system dashboard."""
    try:
        summary_data = get_dashboard_summary()
    except Exception as e:
        # Fallback in case of database error
        return f"<h1>Database Error: Could not load summary data.</h1><p>{e}</p>", 500

    return render_template_string(DASHBOARD_TEMPLATE, summary=summary_data)

if __name__ == '__main__':
    # Ensure all components run in the main application context
    try:
        app.run(debug=True, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping Scheduler and exiting...")
        scheduler.shutdown()

