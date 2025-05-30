import ccxt
import time
import requests
import threading


 
# Binance API credentials (hardcoded for convenience)
API_KEY = '23JIObk7wwSv2laHEb99rEcG2q0ayoDqOZXOIt4iifRmO1RxxbPNZfDA8aUCBYrK'
API_SECRET = 'mWcGT9tO7t0N0quVk6OiANfGtD9PnXcBeb0A5fm63uwO3MJtqTGnFnBf3Qy8honI'

# Initialize the exchange (Binance)
exchange = ccxt.binance({
    'apiKey': API_KEY,  # Replace with your Binance API key
    'secret': API_SECRET,  # Replace with your Binance secret key
    'enableRateLimit': True,  # Respect rate limits
})

# Configurable Parameters
symbol = "FDUSD/USDT"  # Hardcoded symbol for this function
SYMBOL = "DOGE/FDUSD"
TRADE_AMOUNT = 25  # Order size in DOGE
SPREAD_PERCENT = 0.1  # Spread percentage for buy/sell
PROFIT_LOCK_THRESHOLD = 0.5  # Profit threshold before transferring to earn wallet
PROFIT_TICK_THRESHOLD = 1.0  # Profit threshold for showing the green tick emoji (1 INR)
fdusd_to_inr = 86.54
SPREAD_VALUE = 0.00005
STOP_LOSS_OFFSET = 0.00001  # Stop-loss threshold
TAKE_PROFIT_OFFSET = 0.00005  # Take-profit threshold
emergency_offset = 0.00010
# Tracking Balances
last_order_was_buy = False 
total_profit = 0
total_profit_fdusd = 0.0
last_successful_buy_price = None  # Track last successful buy price

# Function to get market price (with bid/ask)
def get_price():
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        bid_price = float(ticker['bid'])  # Best current bid price (sell at this price)
        ask_price = float(ticker['ask'])  # Best current ask price (buy at this price)

        # Calculate Mid Price
        mid_price = (bid_price + ask_price) / 2

        # Define Spread Percentage
        SPREAD_PERCENT = 0.1  # Example: 1% spread

        # Calculate Buy and Sell Prices
        buy_price = bid_price
        sell_price = ask_price + 0.00005

        return {
            'last': float(ticker['last']),  
            'bid': bid_price,    
            'ask': ask_price,     
            'mid': mid_price,  # Mid Price Added
            'buy_price': buy_price,  # Adjusted Buy Price
            'sell_price': sell_price  # Adjusted Sell Price
        }

    except Exception as e:
        print(f"Error fetching price: {e}")
        return None
# Function to get symbol precision
def get_symbol_precision(symbol):
    try:
        markets = exchange.load_markets()
        return {
            'amount': int(markets[symbol]['precision']['amount']),
            'price': int(markets[symbol]['precision']['price'])
       }

    except Exception as e:
        print(f"Error fetching precision: {e}")
        return None


# Function to place a limit order
def place_order(order_type, price, amount):

    try:
        if order_type == "buy":
            order = exchange.create_limit_buy_order(SYMBOL, amount, price)
        else:
            order = exchange.create_limit_sell_order(SYMBOL, amount, price)

        if not order or 'id' not in order:
            print(f"❌ Failed to place {order_type.upper()} order at {price}.")
            return None  # Prevent errors if order_id is missing

        order_id = order['id']
        print(f"📌 Placed {order_type.upper()} order at {price}, Order ID: {order_id}")

        # ✅ Update last buy/sell price immediately after placing order

        # ⏳ Allow time for order status update
        time.sleep(2)
        order_status = exchange.fetch_order(order_id, SYMBOL)

        if order_status['status'] == 'closed':  # ✅ 'closed' is correct, not 'filled'
            print(f"✅ Order {order_id} successfully executed.")
        else:
            # ⏳ Start cancel thread only if order is still open
            cancel_thread = threading.Thread(
                target=cancel_order_after_delay,
                args=(order_id,),
                daemon=False  # Allow thread to run fully
            )
            cancel_thread.start()
            print(f"⏳ Started cancellation thread for Order {order_id}")

        return order  # Exit function after success

    except Exception as e:
        print(f"❌ Error placing {order_type.upper()} order: {e}")
        return None  # Prevents crashes elsewhere

def cancel_order_after_delay(order_id, delay=50):
    """Cancel the order if it's still open after 'delay' seconds."""
    time.sleep(delay)  # Wait without blocking the main thread
   
    try:
        order_status = exchange.fetch_order(order_id, SYMBOL)

        if order_status['status'] == 'open':  # If order is still unfilled
            exchange.cancel_order(order_id, SYMBOL)
            print(f"Order {order_id} canceled after {delay} seconds.")
            return False

        elif order_status['status'] == 'closed':  # Already filled
            print(f"✅ Order {order_id} was already filled.")
            return True
  
    except Exception as e:
        print(f"⚠️ Error checking/canceling order {order_id}: {e}")

        return False
# Function to check balance
def get_balances():
    try:
        balance = exchange.fetch_balance()
        return {
            'DOGE': float(balance['DOGE']['free']),
            'FDUSD': float(balance['FDUSD']['free'])
        }
    except Exception as e:
        print(f"Error fetching balances: {e}")
        return None
# Trading Loop
while True:
    try:
        print("Starting new trade cycle...")

        # Fetch symbol precision
        precision = get_symbol_precision(SYMBOL)
        if precision is None:
             time.sleep(5)
             continue
        amount_precision = precision['amount']
        price_precision = precision['price']

        # Fetch current market price
        price_data = get_price()  # Fetch latest price data

        if price_data:  # Ensure price data is available
            buy_price = price_data['buy_price']
            sell_price = price_data['sell_price']
        stop_loss_price = buy_price + STOP_LOSS_OFFSET  # Set stop-loss price
        take_profit_price = buy_price + TAKE_PROFIT_OFFSET  # Set take-profit price
        emergency_sell_price = buy_price - emergency_offset
        current_price = price_data["last"]

        # Fetch updated balances
        balances = get_balances()
        if balances is None:
            time.sleep(5)
            continue
        doge_balance = balances['DOGE']
        fdusd_balance = balances['FDUSD']
        required_doge_for_sell = TRADE_AMOUNT

        # Round TRADE_AMOUNT to the correct precision
        trade_amount = round(TRADE_AMOUNT, amount_precision)
        
        if fdusd_balance >= (buy_price * TRADE_AMOUNT)* 1.001:

            print(f"enough balanace to buy")

            if not last_order_was_buy:

                order = place_order("buy", buy_price, TRADE_AMOUNT)
 
                if order and "id" in order:

                    order_id = order["id"]

                    print(f"📌 Placed BUY order at {buy_price}, Order ID: {order_id}")
                                                                       
                    last_successful_buy_price = buy_price

            elif last_order_was_buy:

                print(f"checking balance to sell")

                if doge_balance >= TRADE_AMOUNT :

                    print(f"enough balance to sell")
 
                    current_price = price_data["last"]
 
                    if current_price >= take_profit_price:
                        print(f"🎯 Take-Profit hit at {take_profit_price}! Selling...")
                        order = place_order("sell", take_profit_price, TRADE_AMOUNT)
                        if order and "id" in order: 
                            order_id = order["id"]
                            print(f"📌 Placed sell order at {take_profit_price}, Order ID: {order_id}") 
                        last_order_was_buy = False

           #         elif current_price <= stop_loss_price:
           #             print(f"⚠️ Stop-Loss triggered at {stop_loss_price}! Selling...")
           #             order =  place_order("sell", stop_loss_price, TRADE_AMOUNT)
           #            if order and "id" in order:
           #                 order_id = order["id"]
           #                 print(f" 📌 placed sell order at {stop_loss_price}, Order ID: {order_id}")
           #             last_order_was_buy = False
                    elif current_price <= emergency_sell_price: 
                        print(f"EMERGENCY SELLING AT {current_price}, Order ID: {order_id}")
                        order = place_order("sell", current_price, TRADE_AMOUNT)
                        if order and "id" in order:
                            order_id = order["id"]
                            print(f"📌 EMERGENCY sell order at {current_price}, Order ID: {order_id}")    
                        last_order_was_buy = False


            else:

                print(f"insufficient balance to sell, buying")

                order = place_order("buy", buy_price, TRADE_AMOUNT)

                if order and "id" in order:

                    order_id = order["id"]

                    print(f"📌 Placed BUY order at {buy_price},Order ID: {order_id}")

        else:
            print(f"Not enough balance to buy. Checking if we should sell...")

            print(f"checking balance to sell")
                    
            if doge_balance >= TRADE_AMOUNT :
                                      
                print(f"enough balance to sell")

                current_price = price_data["last"]

                if current_price >= take_profit_price:
                    print(f"🎯 Take-Profit hit at {take_profit_price}! Selling...")
                    order = place_order("sell", take_profit_price, TRADE_AMOUNT)
                    if order and "id" in order:
                        order_id = order["id"]
                        print(f"📌 Placed sell order at {take_profit_price}, Order ID: {order_id}")
                        last_order_was_buy = False

       #         elif current_price <= stop_loss_price:
       #             print(f"⚠️ Stop-Loss triggered at {stop_loss_price}! Selling...")
       #             order =  place_order("sell", stop_loss_price, TRADE_AMOUNT)
       #             if order and "id" in order:
       #                 order_id = order["id"]
       #                 print(f" 📌 placed sell order at {stop_loss_price}, Order ID: {order_id}")
       #                 last_order_was_buy = False
                elif current_price <= emergency_sell_price:
                    print(f"EMERGENCY SELLING AT {current_price}, Order ID: {order_id}")
                    order = place_order("sell", current_price, TRADE_AMOUNT)
                    if order and "id" in order:
                        order_id = order["id"]
                        print(f"📌 EMERGENCY sell order at {current_price}, Order ID: {order_id}")
                        last_order_was_buy = False 
                     
    except Exception as e:
        print(f"⚠️ Trade cycle error: {e}")
        time.sleep(5)  # Prevent crash loops
    except ccxt.RateLimitExceeded:
        threading.Thread(target=cancel_order_after_delay, args=(order_id,)).start()
        print("Rate limit exceeded. Retrying after 10 seconds...")
        time.sleep(10)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
