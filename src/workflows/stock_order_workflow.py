from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, BracketOrder
from config.settings import DEFAULT_HOST, PAPER_TRADING_PORT, DEFAULT_CLIENT_ID
from src.orders.history import save_order_to_history

def stock_order_workflow():
    print("\n📈 Stock Bracket Order Workflow")
    
    # Get stock symbol
    symbol = input("Enter stock symbol (e.g., AAPL): ").strip().upper()
    
    # Get action (Buy or Sell)
    action = input("Buy or Sell? (BUY/SELL): ").strip().upper()
    
    # Get quantity
    quantity = int(input("Quantity (e.g., 100): ").strip())
    
    # Get exchange (optional, defaults to SMART)
    exchange = input("Exchange (default: SMART): ").strip().upper()
    if not exchange:
        exchange = "SMART"
    
    # Get currency (optional, defaults to USD)
    currency = input("Currency (press Enter for USD): ").strip().upper()
    if not currency:
        currency = "USD"

    # Ask if user wants bracket order or simple order
    print("\n🎯 Order Type Selection")
    print("1. Simple Order (Market/Limit only)")
    print("2. Bracket Order (with stop loss and take profit)")
    order_choice = int(input("Select order type (1-2): ").strip())
    
    if order_choice == 1:
        # Simple order workflow
        return simple_order_workflow(symbol, action, quantity, exchange, currency)
    
    print("\n🎯 Bracket Order Setup")
    print("This creates a parent order with automatic stop loss and take profit orders")
    
    # Get parent order type
    print("\nParent Order Type:")
    print("1. Market Order")
    print("2. Limit Order")
    parent_type = int(input("Select parent order type (1-2): ").strip())
    
    # Prepare order data for history
    order_data = {
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'exchange': exchange,
        'currency': currency,
        'order_type': 'Bracket Order',
        'order_type_num': 5,
        'instrument_type': 'stock'
    }
    
    if parent_type == 1:
        parent_order = MarketOrder(action, quantity)
        order_data['parent_order_type'] = 'Market'
    else:
        limit_price = float(input("Enter limit price for parent order: ").strip())
        parent_order = LimitOrder(action, quantity, limit_price)
        order_data['parent_order_type'] = 'Limit'
        order_data['limit_price'] = limit_price
    
    # Get stop loss price
    print(f"\n🛑 Stop Loss Setup")
    if action == "BUY":
        stop_loss_price = float(input("Enter stop loss price (below entry price): ").strip())
    else:
        stop_loss_price = float(input("Enter stop loss price (above entry price): ").strip())
    
    # Get take profit price
    print(f"\n💰 Take Profit Setup")
    if action == "BUY":
        take_profit_price = float(input("Enter take profit price (above entry price): ").strip())
    else:
        take_profit_price = float(input("Enter take profit price (below entry price): ").strip())
    
    # Validate bracket prices
    errors = validate_bracket_prices(
        order_data.get('limit_price', 0), 
        stop_loss_price, 
        take_profit_price, 
        action, 
        parent_type
    )
    
    if errors:
        print("\n❌ Price validation errors:")
        for error in errors:
            print(f"   • {error}")
        return
    
    order_data['stop_loss_price'] = stop_loss_price
    order_data['take_profit_price'] = take_profit_price
    
    # Calculate and display risk/reward
    entry_price = order_data.get('limit_price', 0)
    if entry_price > 0:
        ratio, msg = calculate_risk_reward(entry_price, stop_loss_price, take_profit_price, action)
        if ratio:
            print(f"\n📊 {msg}")
            if ratio < 1:
                print("⚠️  Warning: Risk is greater than reward")

    # Display order summary
    print(f"\n📋 Bracket Order Summary:")
    print("=" * 60)
    print(f"Symbol: {symbol}")
    print(f"Exchange: {exchange}")
    print(f"Currency: {currency}")
    print(f"Action: {action}")
    print(f"Quantity: {quantity}")
    print(f"Parent Order: {order_data['parent_order_type']}")
    
    if order_data.get('limit_price'):
        print(f"Entry Price: ${order_data['limit_price']:.2f}")
    print(f"Stop Loss: ${stop_loss_price:.2f}")
    print(f"Take Profit: ${take_profit_price:.2f}")
    
    print("=" * 60)
    
    confirm = input("\n✅ Confirm bracket order? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Order cancelled.")
        return

    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        contract = Stock(symbol, exchange, currency)
        ib.qualifyContracts(contract)
        
        print("\n📤 Submitting bracket order...")
        
        # Create bracket order - this returns a list of Order objects, not Trade objects
        # Create stop loss and take profit order objects
        if action == "BUY":
            stop_loss_order = StopOrder("SELL", quantity, stop_loss_price)
            take_profit_order = LimitOrder("SELL", quantity, take_profit_price)
        else:  # SELL
            stop_loss_order = StopOrder("BUY", quantity, stop_loss_price)
            take_profit_order = LimitOrder("BUY", quantity, take_profit_price)
        

        print(stop_loss_order)
        bracket_orders = BracketOrder(
            parent=parent_order,
            stopLoss=stop_loss_order,
            takeProfit=take_profit_order
        )
        
        # Submit each order in the bracket individually
        trades = []
        order_ids = []
        
        for i, order in enumerate(bracket_orders):
            try:
                print(f"📤 Submitting order {i+1} of {len(bracket_orders)} ({order.orderType})...")
                print(order)
                trade = ib.placeOrder(contract, order)
                trades.append(trade)
                order_ids.append(trade.order.orderId)
                ib.sleep(1)  # Small delay between orders
                
                print(f"   ✅ Order {i+1}: ID {trade.order.orderId}, Type: {order.orderType}")
                
            except Exception as order_error:
                print(f"   ❌ Error with order {i+1}: {order_error}")
                continue
        
        # Wait for all orders to be processed
        ib.sleep(2)
        
        if trades:
            print(f"\n✅ Bracket order submitted! {len(trades)} orders created:")
            
            # Display all order details
            for i, trade in enumerate(trades):
                order_id = trade.order.orderId
                status = trade.orderStatus.status
                order_type = trade.order.orderType
                print(f"   Order {i+1}: ID {order_id}, Type: {order_type}, Status: {status}")
            
            # Store order IDs based on order type
            parent_id = None
            stop_loss_id = None
            take_profit_id = None
            
            for trade in trades:
                if trade.order.orderType in ['MKT', 'LMT']:
                    parent_id = trade.order.orderId
                elif trade.order.orderType == 'STP':
                    stop_loss_id = trade.order.orderId
                elif trade.order.orderType == 'LMT' and trade.order.parentId:
                    take_profit_id = trade.order.orderId
            
            # Store all order IDs
            order_data['parent_order_id'] = parent_id
            order_data['stop_loss_order_id'] = stop_loss_id
            order_data['take_profit_order_id'] = take_profit_id
            order_data['all_order_ids'] = order_ids
            order_data['status'] = 'BRACKET_SUBMITTED'
            order_data['total_orders'] = len(trades)
            
        else:
            print("❌ No orders were successfully submitted")
            order_data['status'] = 'FAILED'
        
        # Save to history
        save_order_to_history(order_data)
        
        # Display final summary
        if trades:
            print("\n🎉 Bracket Order Submission Complete!")
            print("=" * 60)
            print(f"Total Orders Submitted: {len(trades)}")
            if order_data.get('parent_order_id'):
                print(f"Parent Order ID: {order_data['parent_order_id']}")
            if order_data.get('stop_loss_order_id'):
                print(f"Stop Loss Order ID: {order_data['stop_loss_order_id']}")
            if order_data.get('take_profit_order_id'):
                print(f"Take Profit Order ID: {order_data['take_profit_order_id']}")
            print("=" * 60)
            
            # Show next steps
            print("\n📋 What happens next:")
            print("• Parent order will execute first")
            print("• Once filled, stop loss and take profit become active")
            print("• Only one protective order will execute")
            print("• When one executes, the other is automatically cancelled")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        order_data['status'] = 'ERROR'
        order_data['error'] = str(e)
        save_order_to_history(order_data)
    finally:
        ib.disconnect()

def calculate_risk_reward(entry_price, stop_loss_price, take_profit_price, action):
    """Calculate risk/reward ratio"""
    try:
        if action.upper() == "BUY":
            risk = entry_price - stop_loss_price
            reward = take_profit_price - entry_price
        else:  # SELL
            risk = stop_loss_price - entry_price
            reward = entry_price - take_profit_price
        
        if risk <= 0:
            return None, "Invalid risk calculation - check your prices"
        
        ratio = reward / risk
        return ratio, f"Risk/Reward Ratio: {ratio:.2f}:1 (Risk: ${risk:.2f}, Reward: ${reward:.2f})"
    except Exception as e:
        return None, f"Error calculating risk/reward: {e}"

def validate_bracket_prices(entry_price, stop_loss_price, take_profit_price, action, parent_type):
    """Validate bracket order prices make sense"""
    errors = []
    
    try:
        if action.upper() == "BUY":
            if parent_type == 2 and entry_price > 0:  # Limit order
                if stop_loss_price >= entry_price:
                    errors.append("For BUY orders, stop loss must be below entry price")
                if take_profit_price <= entry_price:
                    errors.append("For BUY orders, take profit must be above entry price")
            
            if stop_loss_price >= take_profit_price:
                errors.append("For BUY orders, stop loss must be below take profit")
                
        else:  # SELL
            if parent_type == 2 and entry_price > 0:  # Limit order
                if stop_loss_price <= entry_price:
                    errors.append("For SELL orders, stop loss must be above entry price")
                if take_profit_price >= entry_price:
                    errors.append("For SELL orders, take profit must be below entry price")
            
            if stop_loss_price <= take_profit_price:
                errors.append("For SELL orders, stop loss must be above take profit")
        
        # Basic sanity checks
        if stop_loss_price <= 0:
            errors.append("Stop loss price must be positive")
        if take_profit_price <= 0:
            errors.append("Take profit price must be positive")
            
    except Exception as e:
        errors.append(f"Error validating prices: {e}")
    
    return errors

def show_bracket_order_help():
    """Show help for bracket orders"""
    print("\n📚 Bracket Order Information:")
    print("=" * 60)
    print("🎯 A bracket order combines three orders:")
    print("   1. Parent order (Market or Limit) - your main trade")
    print("   2. Stop loss order - limits your losses")
    print("   3. Take profit order - secures your gains")
    print()
    print("💡 How it works:")
    print("   • Parent order executes first")
    print("   • Stop loss and take profit become active")
    print("   • Only ONE of the protective orders will execute")
    print("   • When one executes, the other is cancelled")
    print()
    print("⚠️  Important for pricing:")
    print("   • BUY: Stop loss < Entry < Take profit")
    print("   • SELL: Take profit < Entry < Stop loss")
    print("   • Always consider risk/reward ratio")
    print("=" * 60)

def simple_order_workflow(symbol, action, quantity, exchange, currency):
    """Handle simple order workflow (non-bracket)"""
    print("\n📋 Simple Order Setup")
    
    # Get order type
    print("\nOrder Type:")
    print("1. Market Order")
    print("2. Limit Order")
    print("3. Stop Order")
    print("4. Stop Limit Order")
    order_type = int(input("Select order type (1-4): ").strip())
    
    # Prepare order data
    order_data = {
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'exchange': exchange,
        'currency': currency,
        'instrument_type': 'stock',
        'order_type_num': order_type
    }
    
    # Create appropriate order
    if order_type == 1:
        order = MarketOrder(action, quantity)
        order_data['order_type'] = 'Market Order'
    elif order_type == 2:
        limit_price = float(input("Enter limit price: ").strip())
        order = LimitOrder(action, quantity, limit_price)
        order_data['order_type'] = 'Limit Order'
        order_data['limit_price'] = limit_price
    elif order_type == 3:
        stop_price = float(input("Enter stop price: ").strip())
        order = StopOrder(action, quantity, stop_price)
        order_data['order_type'] = 'Stop Order'
        order_data['stop_price'] = stop_price
    elif order_type == 4:
        stop_price = float(input("Enter stop price: ").strip())
        limit_price = float(input("Enter limit price: ").strip())
        order = StopLimitOrder(action, quantity, limit_price, stop_price)
        order_data['order_type'] = 'Stop Limit Order'
        order_data['stop_price'] = stop_price
        order_data['limit_price'] = limit_price
    
    # Display order summary
    print(f"\n📋 Order Summary:")
    print("=" * 60)
    print(f"Symbol: {symbol}")
    print(f"Exchange: {exchange}")
    print(f"Currency: {currency}")
    print(f"Action: {action}")
    print(f"Quantity: {quantity}")
    print(f"Order Type: {order_data['order_type']}")
    if order_data.get('limit_price'):
        print(f"Limit Price: ${order_data['limit_price']:.2f}")
    if order_data.get('stop_price'):
        print(f"Stop Price: ${order_data['stop_price']:.2f}")
    print("=" * 60)
    
    confirm = input("\n✅ Confirm order? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Order cancelled.")
        return

    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        contract = Stock(symbol, exchange, currency)
        ib.qualifyContracts(contract)
        
        print("\n📤 Submitting order...")
        trade = ib.placeOrder(contract, order)
        
        print(f"✅ Order submitted! Order ID: {trade.order.orderId}")
        print(f"Status: {trade.orderStatus.status}")
        
        order_data['order_id'] = trade.order.orderId
        order_data['status'] = trade.orderStatus.status
        
    except Exception as e:
        print(f"❌ Error: {e}")
        order_data['status'] = 'ERROR'
        order_data['error'] = str(e)
    finally:
        save_order_to_history(order_data)
        ib.disconnect()

# If running directly, show help and run workflow
if __name__ == "__main__":
    show_bracket_order_help()
    stock_order_workflow()