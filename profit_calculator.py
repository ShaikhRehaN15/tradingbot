import ccxt
import time
from datetime import datetime, timedelta

# CONFIGURE YOUR EXCHANGE
exchange = ccxt.binance({
    'apiKey': '23JIObk7wwSv2laHEb99rEcG2q0ayoDqOZXOIt4iifRmO1RxxbPNZfDA8aUCBYrK',
    'secret': 'mWcGT9tO7t0N0quVk6OiANfGtD9PnXcBeb0A5fm63uwO3MJtqTGnFnBf3Qy8honI',
    'options': {'defaultType': 'spot'}
})

SYMBOL = 'DOGE/FDUSD'  # Change if needed

# Function to fetch trades in the last 24 hours
def get_trade_history():
    try:
        since = exchange.milliseconds() - (24 * 60 * 60 * 1000)  # 24 hours ago
        trades = exchange.fetch_my_trades(SYMBOL, since)
        return trades
    except Exception as e:
        print(f"⚠️ Error fetching trades: {e}")
        return []

# Function to calculate profit and trade count (Buy+Sell as One Trade)
def calculate_profit():
    trades = get_trade_history()

    if not trades:
        print("⚠️ No trades found in the last 24 hours.")
        return

    total_profit = 0
    buy_total = 0
    sell_total = 0
    buy_count = 0
    sell_count = 0

    for trade in trades:
        price = float(trade['price'])
        cost = float(trade['cost'])
        
        if trade['side'] == 'buy':
            buy_total += cost
            buy_count += 1
        elif trade['side'] == 'sell':
            sell_total += cost
            sell_count += 1

    total_profit = sell_total - buy_total

    # Count "trades" as pairs of buy+sell
    full_trade_count = min(buy_count, sell_count)  # Each buy should match a sell

    print(f"📊 **Trade Summary (Last 24h)**")
    print(f"🔹 Total Trades Executed (Buy+Sell Pairs): {full_trade_count}")
    print(f"💰 Total Profit: {total_profit:.2f} FDUSD")

# Run the script
calculate_profit()
