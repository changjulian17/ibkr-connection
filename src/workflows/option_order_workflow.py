from ib_insync import IB, Option, MarketOrder, LimitOrder, StopOrder, StopLimitOrder
from config.settings import DEFAULT_HOST, PAPER_TRADING_PORT, DEFAULT_CLIENT_ID
from src.orders.history import save_order_to_history

def option_order_workflow():
    print("\n📊 Option Order Workflow")
    symbol = input("Enter underlying symbol (e.g., AAPL): ").strip().upper()
    expiry = input("Enter expiry date (YYYYMMDD, e.g., 20241220): ").strip()
    strike = float(input("Enter strike price (e.g., 150.0): ").strip())
    
    print("\nOption Type:")
    print("C - Call")
    print("P - Put")
    right = input("Enter option type (C/P): ").strip().upper()
    
    action = input("Buy or Sell? (BUY/SELL): ").strip().upper()
    quantity = int(input("Quantity (e.g., 1): ").strip())

    print("\nOrder Type:")
    print("1. Market Order")
    print("2. Limit Order")
    print("3. Stop Order")
    print("4. Stop Limit Order")
    order_type = int(input("Select order type (1-4): ").strip())

    order_type_names = {
        1: "Market Order",
        2: "Limit Order", 
        3: "Stop Order",
        4: "Stop Limit Order"
    }

    # Prepare order data for history
    order_data = {
        'symbol': symbol,
        'expiry': expiry,
        'strike': strike,
        'right': right,
        'action': action,
        'quantity': quantity,
        'order_type': order_type_names[order_type],
        'order_type_num': order_type,
        'instrument_type': 'option'
    }

    order = None
    if order_type == 1:
        order = MarketOrder(action, quantity)
    elif order_type == 2:
        limit_price = float(input("Enter limit price: ").strip())
        order = LimitOrder(action, quantity, limit_price)
        order_data['limit_price'] = limit_price
    elif order_type == 3:
        stop_price = float(input("Enter stop price: ").strip())
        order = StopOrder(action, quantity, stop_price)
        order_data['stop_price'] = stop_price
    elif order_type == 4:
        stop_price = float(input("Enter stop price: ").strip())
        limit_price = float(input("Enter limit price: ").strip())
        order = StopLimitOrder(action, quantity, stop_price, limit_price)
        order_data['stop_price'] = stop_price
        order_data['limit_price'] = limit_price
    else:
        print("Invalid order type.")
        return

    # Display order summary
    print(f"\n📋 Order Summary:")
    print(f"Symbol: {symbol}")
    print(f"Expiry: {expiry}")
    print(f"Strike: {strike}")
    print(f"Right: {right}")
    print(f"Action: {action}")
    print(f"Quantity: {quantity}")
    print(f"Order Type: {order_type_names[order_type]}")
    
    confirm = input("\nConfirm order? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Order cancelled.")
        return

    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        contract = Option(symbol, expiry, strike, right, 'SMART')
        ib.qualifyContracts(contract)
        print("\nSubmitting order...")
        trade = ib.placeOrder(contract, order)
        ib.sleep(2)
        
        # Add result info to order data
        order_data['status'] = trade.orderStatus.status
        order_data['order_id'] = trade.order.orderId
        
        print(f"✅ Order submitted! Status: {trade.orderStatus.status}, Order ID: {trade.order.orderId}")
        
        # Save to history
        save_order_to_history(order_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        order_data['status'] = 'ERROR'
        order_data['error'] = str(e)
        save_order_to_history(order_data)
    finally:
        ib.disconnect()