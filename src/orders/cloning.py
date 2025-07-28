"""Order Cloning Functionality"""

from ib_insync import IB, Forex, Stock, Option, MarketOrder, LimitOrder, StopOrder, StopLimitOrder
from .history import load_order_history, save_order_to_history, display_order_history
from config.settings import DEFAULT_HOST, PAPER_TRADING_PORT, DEFAULT_CLIENT_ID

def clone_order():
    """Clone an existing order with editable parameters"""
    history = display_order_history()
    if not history:
        return
    
    # Get order to clone
    while True:
        try:
            order_id = int(input("\nEnter order ID to clone: ").strip())
            original_order = next((o for o in history if o['id'] == order_id), None)
            if original_order:
                break
            else:
                print("❌ Order ID not found")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print(f"\n📋 Cloning Order #{order_id}")
    print("=" * 60)
    
    # Display original order details
    print("Original Order:")
    for key, value in original_order.items():
        if key not in ['id', 'timestamp']:
            print(f"  {key}: {value}")
    
    # Get edited parameters
    new_order_data = get_edited_parameters(original_order)
    
    # Show confirmation
    print(f"\n📋 New Order Summary:")
    print("=" * 60)
    for key, value in new_order_data.items():
        if key not in ['order_type_num']:
            print(f"{key.replace('_', ' ').title()}: {value}")
    print("=" * 60)
    
    confirm = input("\n✅ Submit this cloned order? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Order cancelled")
        return
    
    # Submit the cloned order
    submit_cloned_order(new_order_data)

def get_edited_parameters(original_order):
    """Get edited parameters for cloned order"""
    print("\n" + "=" * 60)
    print("🔧 Edit Parameters (press Enter to keep original value)")
    print("=" * 60)
    
    # Edit symbol
    new_symbol = input(f"Symbol [{original_order['symbol']}]: ").strip().upper()
    if not new_symbol:
        new_symbol = original_order['symbol']
    
    # Edit action
    current_action = original_order['action']
    action_input = input(f"Action (BUY/SELL) [{current_action}]: ").strip().upper()
    new_action = action_input if action_input in ['BUY', 'SELL'] else current_action
    
    # Edit quantity
    try:
        qty_input = input(f"Quantity [{original_order['quantity']}]: ").strip()
        new_quantity = int(qty_input) if qty_input else original_order['quantity']
    except ValueError:
        new_quantity = original_order['quantity']
    
    # Edit order type
    order_types = {
        1: "Market Order",
        2: "Limit Order", 
        3: "Stop Order",
        4: "Stop Limit Order"
    }
    
    print("\nOrder Types:")
    for num, name in order_types.items():
        print(f"{num}. {name}")
    
    current_type_num = original_order.get('order_type_num', 1)
    try:
        type_input = input(f"Order type (1-4) [{current_type_num}]: ").strip()
        new_order_type = int(type_input) if type_input else current_type_num
        if new_order_type not in [1, 2, 3, 4]:
            new_order_type = current_type_num
    except ValueError:
        new_order_type = current_type_num
    
    # Edit prices based on order type
    new_limit_price = None
    new_stop_price = None
    
    if new_order_type in [2, 4]:  # Limit or Stop Limit
        try:
            limit_input = input(f"Limit price [{original_order.get('limit_price', '')}]: ").strip()
            new_limit_price = float(limit_input) if limit_input else original_order.get('limit_price')
        except ValueError:
            new_limit_price = original_order.get('limit_price')
    
    if new_order_type in [3, 4]:  # Stop or Stop Limit
        try:
            stop_input = input(f"Stop price [{original_order.get('stop_price', '')}]: ").strip()
            new_stop_price = float(stop_input) if stop_input else original_order.get('stop_price')
        except ValueError:
            new_stop_price = original_order.get('stop_price')
    
    # Create new order data
    new_order_data = {
        'symbol': new_symbol,
        'action': new_action,
        'quantity': new_quantity,
        'order_type': order_types[new_order_type],
        'order_type_num': new_order_type,
        'instrument_type': original_order.get('instrument_type', 'forex')
    }
    
    # Add additional parameters for specific instruments
    if original_order.get('instrument_type') == 'stock':
        new_order_data['exchange'] = original_order.get('exchange', 'SMART')
        new_order_data['currency'] = original_order.get('currency', 'USD')
    elif original_order.get('instrument_type') == 'option':
        new_order_data['expiry'] = original_order.get('expiry')
        new_order_data['strike'] = original_order.get('strike')
        new_order_data['right'] = original_order.get('right')
    
    if new_limit_price:
        new_order_data['limit_price'] = new_limit_price
    if new_stop_price:
        new_order_data['stop_price'] = new_stop_price
        
    return new_order_data

def submit_cloned_order(order_data):
    """Submit a cloned order"""
    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        print("✅ Connected to IBKR!")
        
        # Create contract based on instrument type
        contract = create_contract(order_data)
        if not contract:
            return
        
        ib.qualifyContracts(contract)
        
        # Create order
        order = create_order_from_data(order_data)
        if not order:
            return
        
        # Submit order
        print("\n📤 Submitting cloned order...")
        trade = ib.placeOrder(contract, order)
        ib.sleep(2)
        
        # Update order data with results
        order_data['status'] = trade.orderStatus.status
        order_data['order_id'] = trade.order.orderId
        
        print(f"✅ Cloned order submitted!")
        print(f"Order ID: {trade.order.orderId}")
        print(f"Status: {trade.orderStatus.status}")
        
        # Save to history
        save_order_to_history(order_data)
        
    except Exception as e:
        print(f"❌ Error submitting cloned order: {e}")
        order_data['status'] = 'ERROR'
        order_data['error'] = str(e)
        save_order_to_history(order_data)
    finally:
        ib.disconnect()

def create_contract(order_data):
    """Create contract from order data"""
    try:
        if order_data['instrument_type'] == 'forex':
            return Forex(order_data['symbol'])
        elif order_data['instrument_type'] == 'stock':
            return Stock(order_data['symbol'], 
                        order_data.get('exchange', 'SMART'), 
                        order_data.get('currency', 'USD'))
        elif order_data['instrument_type'] == 'option':
            return Option(order_data['symbol'],
                         order_data['expiry'],
                         order_data['strike'],
                         order_data['right'],
                         'SMART')
        else:
            print(f"❌ Unsupported instrument type: {order_data['instrument_type']}")
            return None
    except Exception as e:
        print(f"❌ Error creating contract: {e}")
        return None

def create_order_from_data(order_data):
    """Create order from order data"""
    try:
        if order_data['order_type_num'] == 1:  # Market
            return MarketOrder(order_data['action'], order_data['quantity'])
        elif order_data['order_type_num'] == 2:  # Limit
            return LimitOrder(order_data['action'], order_data['quantity'], order_data['limit_price'])
        elif order_data['order_type_num'] == 3:  # Stop
            return StopOrder(order_data['action'], order_data['quantity'], order_data['stop_price'])
        elif order_data['order_type_num'] == 4:  # Stop Limit
            return StopLimitOrder(order_data['action'], order_data['quantity'], 
                                order_data['stop_price'], order_data['limit_price'])
        else:
            print(f"❌ Invalid order type: {order_data['order_type_num']}")
            return None
    except Exception as e:
        print(f"❌ Error creating order: {e}")
        return None

def quick_clone_order(order_id, symbol=None, quantity=None, action=None):
    """Quick clone with minimal parameter changes"""
    history = load_order_history()
    original_order = next((o for o in history if o['id'] == order_id), None)
    
    if not original_order:
        print(f"❌ Order ID {order_id} not found")
        return None
    
    # Clone with modifications
    new_order_data = original_order.copy()
    new_order_data.pop('id', None)
    new_order_data.pop('timestamp', None)
    new_order_data.pop('order_id', None)
    
    # Apply modifications
    if symbol:
        new_order_data['symbol'] = symbol
    if quantity:
        new_order_data['quantity'] = quantity
    if action:
        new_order_data['action'] = action
    
    return submit_cloned_order(new_order_data)