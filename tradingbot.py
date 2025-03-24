import ccxt
import time
import threading

# Binance API credentials
API_KEY = "23JIObk7wwSv2laHEb99rEcG2q0ayoDqOZXOIt4iifRmO1RxxbPNZfDA8aUCBYrK"
API_SECRET = "mWcGT9tO7t0N0quVk6OiANfGtD9PnXcBeb0A5fm63uwO3MJtqTGnFnBf3Qy8honI"

# Initialize Binance exchange
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# Configurable Parameters
symbol = "DOGE/FDUSD"
order_size = 10  # Adjust based on your balance
profit_percent = 0.5  # Desired profit percentage
order_timeout = 60  # Time in seconds before canceling an order

last_order_was_buy = False
last_buy_price = None


def place_order(order_type, price=None):
    try:
        if order_type == "buy":
            order = exchange.create_market_buy_order(symbol, order_size)
            print(f"Placed BUY order at {order['price']}")
            return order['price']
        elif order_type == "sell":
            order = exchange.create_market_sell_order(symbol, order_size)
            print(f"Placed SELL order at {order['price']}")
            return order['price']
    except Exception as e:
        print(f"Error placing {order_type} order: {e}")
        return None


def trade_cycle():
    global last_order_was_buy, last_buy_price
    while True:
        print("Starting new trade cycle...")
        time.sleep(2)  # Small delay to prevent excessive API calls

        try:
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if not last_order_was_buy:
                last_buy_price = place_order("buy")
                if last_buy_price:
                    last_order_was_buy = True
            else:
                target_price = last_buy_price * (1 + profit_percent / 100)
                if current_price >= target_price:
                    place_order("sell")
                    last_order_was_buy = False
                    last_buy_price = None
        except Exception as e:
            print(f"Error in trade cycle: {e}")

        time.sleep(5)  # Delay before the next cycle


if __name__ == "__main__":
    trade_cycle()
