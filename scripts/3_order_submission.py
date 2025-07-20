#!/usr/bin/env python3
"""
Order Submission Utility - Submit orders through IBKR using ib_insync

Enhanced version with order history and cloning functionality.
"""

import sys
import os
# Add the parent directory to the path so we can import from config and src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ib_insync import IB, Forex, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order

# Import settings
from config.settings import (
    DEFAULT_HOST,
    PAPER_TRADING_PORT,
    DEFAULT_CLIENT_ID,
    ORDER_TYPES,
    DEFAULT_QUANTITIES,
    DEFAULT_EXCHANGES,
    DEFAULT_CURRENCIES,
    MAX_ORDER_VALUE,
    TABLE_WIDTH,
    MARKET_DATA_TIMEOUT
)

# Import workflows and history functionality
from src.workflows.forex_order_workflow import forex_order_workflow
from src.workflows.stock_order_workflow import stock_order_workflow
from src.workflows.option_order_workflow import option_order_workflow
from src.orders.history import display_order_history, search_orders, get_pending_orders_from_ibkr
from src.orders.cloning import clone_order

def connect_to_ibkr():
    """Connect to IBKR using configured settings"""
    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        print("✅ Connected to IBKR!")
        return ib
    except Exception as e:
        print(f"❌ Failed to connect to IBKR: {e}")
        return None

def get_forex_contract(symbol):
    """Create and qualify forex contract"""
    try:
        contract = Forex(symbol, DEFAULT_EXCHANGES['forex'])
        return contract
    except Exception as e:
        print(f"❌ Error creating contract for {symbol}: {e}")
        return None

def get_current_quote(ib, symbol):
    """Get current market quote for the symbol"""
    try:
        contract = get_forex_contract(symbol)
        if not contract:
            return None
            
        ib.qualifyContracts(contract)
        ticker = ib.reqMktData(contract, '', False, False)
        ib.sleep(MARKET_DATA_TIMEOUT)  # Use configured timeout
        
        return ticker
    except Exception as e:
        print(f"❌ Error getting quote for {symbol}: {e}")
        return None

def display_quote(ticker, symbol):
    """Display current market quote"""
    if not ticker:
        print(f"❌ No market data available for {symbol}")
        return
        
    print(f"\n📊 Current Market Data for {symbol}:")
    print("=" * 40)
    
    if ticker.bid and ticker.bid > 0:
        print(f"Bid: {ticker.bid:.5f}")
    if ticker.ask and ticker.ask > 0:
        print(f"Ask: {ticker.ask:.5f}")
    if ticker.last and str(ticker.last).lower() != 'nan':
        print(f"Last: {ticker.last:.5f}")
    
    if ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
        mid = (ticker.bid + ticker.ask) / 2
        spread = ticker.ask - ticker.bid
        print(f"Mid: {mid:.5f}")
        print(f"Spread: {spread:.5f}")
    
    print("=" * 40)

def get_symbol_input():
    """Get forex symbol from user"""
    g10_pairs = [
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD",
        "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    print("\n💱 Select forex pair:")
    print("=" * 30)
    
    for i, pair in enumerate(g10_pairs, 1):
        print(f"{i:2d}. {pair}")
    print("12. Enter custom forex pair")
    
    while True:
        try:
            choice = int(input("\nEnter choice (1-12): ").strip())
            if 1 <= choice <= 11:
                return g10_pairs[choice - 1]
            elif choice == 12:
                while True:
                    symbol = input("Enter forex pair (e.g., USDSGD): ").strip().upper()
                    if len(symbol) == 6:
                        return symbol
                    else:
                        print("❌ Forex symbol should be 6 characters")
            else:
                print("❌ Please enter a number between 1-12")
        except ValueError:
            print("❌ Please enter a valid number")

def get_order_side():
    """Get order side (BUY/SELL)"""
    print("\n📈 Order Side:")
    print("1. BUY")
    print("2. SELL")
    
    while True:
        try:
            choice = int(input("\nEnter choice (1-2): ").strip())
            if choice == 1:
                return "BUY"
            elif choice == 2:
                return "SELL"
            else:
                print("❌ Please enter 1 or 2")
        except ValueError:
            print("❌ Please enter a valid number")

def get_quantity(instrument_type='forex'):
    """Get order quantity with default suggestion"""
    default_qty = DEFAULT_QUANTITIES.get(instrument_type, 10000)
    
    while True:
        try:
            qty_input = input(f"\n💰 Enter quantity (default: {default_qty:,}): ").strip()
            if not qty_input:
                return default_qty
            
            quantity = float(qty_input)
            if quantity > 0:
                return int(quantity)
            else:
                print("❌ Quantity must be positive")
        except ValueError:
            print("❌ Please enter a valid number")

def get_order_type():
    """Get order type using configured ORDER_TYPES"""
    print("\n📋 Order Type:")
    for num, name in ORDER_TYPES.items():
        description = {
            1: "(immediate execution)",
            2: "(specific price)",
            3: "(stop loss)",
            4: "(stop with limit)"
        }
        print(f"{num}. {name} {description.get(num, '')}")
    
    while True:
        try:
            choice = int(input("\nEnter choice (1-4): ").strip())
            if choice in ORDER_TYPES:
                return choice
            else:
                print("❌ Please enter a number between 1-4")
        except ValueError:
            print("❌ Please enter a valid number")

def get_price(prompt):
    """Get price from user"""
    while True:
        try:
            price = float(input(f"\n💲 {prompt}: ").strip())
            if price > 0:
                return price
            else:
                print("❌ Price must be positive")
        except ValueError:
            print("❌ Please enter a valid price")

def create_order(order_type, action, quantity, **kwargs):
    """Create order based on type"""
    if order_type == 1:  # Market Order
        return MarketOrder(action, quantity)
    elif order_type == 2:  # Limit Order
        return LimitOrder(action, quantity, kwargs['limit_price'])
    elif order_type == 3:  # Stop Order
        return StopOrder(action, quantity, kwargs['stop_price'])
    elif order_type == 4:  # Stop Limit Order
        return StopLimitOrder(action, quantity, kwargs['stop_price'], kwargs['limit_price'])

def validate_order_value(quantity, price, symbol):
    """Validate order value against risk limits"""
    order_value = quantity * price
    if order_value > MAX_ORDER_VALUE:
        print(f"⚠️ Warning: Order value ${order_value:,.2f} exceeds limit of ${MAX_ORDER_VALUE:,.2f}")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        return confirm in ['y', 'yes']
    return True

def confirm_order(symbol, action, quantity, order_type_name, **order_details):
    """Display order confirmation"""
    print("\n" + "="*50)
    print("📋 ORDER CONFIRMATION")
    print("="*50)
    print(f"Symbol:     {symbol}")
    print(f"Action:     {action}")
    print(f"Quantity:   {quantity:,}")
    print(f"Order Type: {order_type_name}")
    
    for key, value in order_details.items():
        if value:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("="*50)
    
    while True:
        confirm = input("\n✅ Confirm order? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return True
        elif confirm in ['n', 'no']:
            return False
        else:
            print("❌ Please enter y or n")

def submit_order(ib, contract, order):
    """Submit order to IBKR"""
    try:
        print("\n📤 Submitting order...")
        trade = ib.placeOrder(contract, order)
        
        # Wait for order status
        ib.sleep(2)
        
        print(f"✅ Order submitted successfully!")
        print(f"Order ID: {trade.order.orderId}")
        print(f"Status: {trade.orderStatus.status}")
        
        return trade
    except Exception as e:
        print(f"❌ Error submitting order: {e}")
        return None

def search_orders_menu():
    """Search orders interface"""
    print("\n🔍 Search Orders")
    print("=" * 30)
    
    symbol = input("Symbol (leave blank for all): ").strip().upper()
    
    print("\nInstrument Type:")
    print("1. All")
    print("2. Forex") 
    print("3. Stock")
    print("4. Option")
    
    choice = input("Enter choice (1-4): ").strip()
    instrument_map = {'2': 'forex', '3': 'stock', '4': 'option'}
    instrument_type = instrument_map.get(choice)
    
    action = input("Action (BUY/SELL, leave blank for all): ").strip().upper()
    
    results = search_orders(
        symbol=symbol if symbol else None,
        instrument_type=instrument_type,
        action=action if action else None
    )
    
    if results:
        print(f"\n📋 Found {len(results)} matching orders:")
        print("=" * TABLE_WIDTH)
        print(f"{'ID':<3} {'Date':<12} {'Symbol':<10} {'Action':<4} {'Qty':<8} {'Type':<12} {'Status':<10}")
        print("-" * TABLE_WIDTH)
        
        for order in results[-20:]:  # Show last 20 results
            date_str = order['timestamp'][:10]
            print(f"{order['id']:<3} {date_str:<12} {order['symbol']:<10} {order['action']:<4} "
                  f"{order['quantity']:<8} {order['order_type']:<12} {order.get('status', 'N/A'):<10}")
        print("=" * TABLE_WIDTH)
    else:
        print("📭 No orders found matching criteria")

def cancel_orders_menu():
    """Cancel orders interface - using live IBKR data"""
    print("\n❌ Cancel Orders")
    print("=" * 30)
    
    # Get pending orders from IBKR account
    print("🔄 Fetching pending orders from IBKR...")
    pending = get_pending_orders_from_ibkr()
    
    if not pending:
        print("📭 No pending orders found in your account")
        return
    
    print(f"\n📋 Pending Orders ({len(pending)} found):")
    print("=" * 120)
    print(f"{'#':<3} {'Order ID':<10} {'Symbol':<12} {'Action':<6} {'Qty':<8} {'Type':<12} "
          f"{'Status':<15} {'Limit':<10} {'Stop':<10}")
    print("-" * 120)
    
    for i, order in enumerate(pending, 1):
        limit_price = order.get('limit_price', '')
        stop_price = order.get('stop_price', '')
        limit_str = f"{limit_price:.4f}" if limit_price else "-"
        stop_str = f"{stop_price:.4f}" if stop_price else "-"
        
        print(f"{i:<3} {order['order_id']:<10} {order['symbol']:<12} {order['action']:<6} "
              f"{order['quantity']:<8} {order['order_type']:<12} {order['status']:<15} "
              f"{limit_str:<10} {stop_str:<10}")
    
    print("=" * TABLE_WIDTH)
    
    # Get cancellation choice
    print("\nCancellation Options:")
    print("1. Cancel specific order by number")
    print("2. Cancel by Order ID")
    print("3. Cancel all pending orders")
    print("4. Refresh order list")
    print("5. Back to main menu")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        try:
            order_num = int(input("Enter order number to cancel: ").strip())
            if 1 <= order_num <= len(pending):
                order = pending[order_num - 1]
                cancel_single_order_live(order)
            else:
                print("❌ Invalid order number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    elif choice == "2":
        order_id = input("Enter Order ID to cancel: ").strip()
        try:
            order_id = int(order_id)
            # Find the order in pending list
            target_order = next((o for o in pending if o['order_id'] == order_id), None)
            if target_order:
                cancel_single_order_live(target_order)
            else:
                print(f"❌ Order ID {order_id} not found in pending orders")
        except ValueError:
            print("❌ Please enter a valid Order ID")
    
    elif choice == "3":
        confirm = input(f"⚠️  Cancel ALL {len(pending)} pending orders? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            cancel_all_pending_orders_live(pending)
        else:
            print("❌ Cancelled")
    
    elif choice == "4":
        cancel_orders_menu()  # Refresh by calling the function again
    
    elif choice == "5":
        return
    else:
        print("❌ Invalid choice")

def cancel_single_order(order_data):
    """Cancel a single order"""
    ib = connect_to_ibkr()
    if not ib:
        return
    
    try:
        # Get order ID(s) to cancel
        order_ids = []
        
        if order_data.get('order_id'):
            order_ids.append(order_data['order_id'])
        
        # For bracket orders, cancel all related orders
        if order_data.get('order_type') == 'Bracket Order':
            if order_data.get('parent_order_id'):
                order_ids.append(order_data['parent_order_id'])
            if order_data.get('stop_loss_order_id'):
                order_ids.append(order_data['stop_loss_order_id'])
            if order_data.get('take_profit_order_id'):
                order_ids.append(order_data['take_profit_order_id'])
        
        if not order_ids:
            print("❌ No valid order IDs found")
            return
        
        print(f"\n📋 Cancelling order(s): {order_ids}")
        
        success_count = 0
        for order_id in order_ids:
            try:
                # Create a dummy order object with the ID for cancellation
                from ib_insync import Order
                cancel_order = Order()
                cancel_order.orderId = order_id
                
                ib.cancelOrder(cancel_order)
                print(f"✅ Cancellation request sent for Order ID: {order_id}")
                success_count += 1
                ib.sleep(0.5)  # Small delay between cancellations
            except Exception as e:
                print(f"❌ Error cancelling Order ID {order_id}: {e}")
        
        if success_count > 0:
            print(f"\n🎉 Successfully sent {success_count} cancellation request(s)")
            print("⏳ Please check order status to confirm cancellation")
            
            # Update order status in history
            from src.orders.history import update_order_status
            update_order_status(order_data['id'], 'CANCEL_REQUESTED')
        
    except Exception as e:
        print(f"❌ Error during cancellation: {e}")
    finally:
        ib.disconnect()

def cancel_order_by_id(order_id):
    """Cancel order by specific ID"""
    ib = connect_to_ibkr()
    if not ib:
        return
    
    try:
        print(f"\n📋 Cancelling Order ID: {order_id}")
        
        # Create a dummy order object with the ID for cancellation
        from ib_insync import Order
        cancel_order = Order()
        cancel_order.orderId = order_id
        
        ib.cancelOrder(cancel_order)
        print(f"✅ Cancellation request sent for Order ID: {order_id}")
        print("⏳ Please check order status to confirm cancellation")
        
    except Exception as e:
        print(f"❌ Error cancelling Order ID {order_id}: {e}")
    finally:
        ib.disconnect()

def cancel_single_order_live(order_info):
    """Cancel a single order using live trade object"""
    ib = connect_to_ibkr()
    if not ib:
        return
    
    try:
        trade = order_info['trade']
        order_id = order_info['order_id']
        
        print(f"\n📋 Cancelling Order ID: {order_id} ({order_info['symbol']} {order_info['action']})")
        
        # Cancel the order using the trade object
        ib.cancelOrder(trade.order)
        ib.sleep(1)  # Wait for cancellation to process
        
        print(f"✅ Cancellation request sent for Order ID: {order_id}")
        print("⏳ Checking cancellation status...")
        
        # Check if cancellation was successful
        ib.sleep(2)
        updated_trades = ib.openTrades()
        still_pending = any(t.order.orderId == order_id and 
                          t.orderStatus.status in ['PreSubmitted', 'Submitted', 'PendingSubmit'] 
                          for t in updated_trades)
        
        if not still_pending:
            print(f"🎉 Order {order_id} successfully cancelled!")
        else:
            print(f"⚠️  Order {order_id} cancellation is being processed...")
        
    except Exception as e:
        print(f"❌ Error cancelling Order ID {order_info['order_id']}: {e}")
    finally:
        ib.disconnect()

def cancel_all_pending_orders_live(pending_orders):
    """Cancel all pending orders using live trade objects"""
    ib = connect_to_ibkr()
    if not ib:
        return
    
    try:
        total_cancelled = 0
        
        print(f"\n📋 Cancelling {len(pending_orders)} orders...")
        
        for order_info in pending_orders:
            try:
                trade = order_info['trade']
                order_id = order_info['order_id']
                
                # Cancel using the trade object
                ib.cancelOrder(trade.order)
                print(f"✅ Cancelled Order ID: {order_id} ({order_info['symbol']})")
                total_cancelled += 1
                ib.sleep(0.5)  # Small delay between cancellations
                
            except Exception as e:
                print(f"❌ Error cancelling Order ID {order_info['order_id']}: {e}")
        
        print(f"\n🎉 Sent cancellation requests for {total_cancelled} orders")
        print("⏳ Please allow a few seconds for all cancellations to process...")
        
        # Check final status
        ib.sleep(3)
        remaining_trades = ib.openTrades()
        remaining_count = len([t for t in remaining_trades if 
                              t.orderStatus.status in ['PreSubmitted', 'Submitted', 'PendingSubmit']])
        
        print(f"📊 {remaining_count} orders still pending after cancellation attempts")
        
    except Exception as e:
        print(f"❌ Error during bulk cancellation: {e}")
    finally:
        ib.disconnect()

def cancel_order_by_id_live(order_id):
    """Cancel order by specific ID using live data"""
    print(f"\n🔄 Looking for Order ID {order_id} in your account...")
    
    pending = get_pending_orders_from_ibkr()
    target_order = next((o for o in pending if o['order_id'] == order_id), None)
    
    if target_order:
        cancel_single_order_live(target_order)
    else:
        print(f"❌ Order ID {order_id} not found in pending orders")
        print("💡 Use option 4 to refresh the order list")

def show_main_menu():
    """Display main menu"""
    print("\n🚀 IBKR Order Submission with History")
    print("=" * 50)
    print("1. Submit Forex Order")
    print("2. Submit Stock Order") 
    print("3. Submit Option Order")
    print("4. View Order History")
    print("5. Clone Previous Order")
    print("6. Search Orders")
    print("7. Cancel Orders")
    print("8. Exit")

def main():
    """Main application loop"""
    while True:
        show_main_menu()
        choice = input("\nEnter choice (1-8): ").strip()
        
        if choice == "1":
            forex_order_workflow()
        elif choice == "2":
            stock_order_workflow()
        elif choice == "3":
            option_order_workflow()
        elif choice == "4":
            display_order_history()
        elif choice == "5":
            clone_order()
        elif choice == "6":
            search_orders_menu()
        elif choice == "7":
            cancel_orders_menu()
        elif choice == "8":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-8.")
        
        input("\nPress Enter to continue...")

def show_order_info():
    """Show order information"""
    print("\n📚 Order Types Information:")
    print("=" * 50)
    for num, name in ORDER_TYPES.items():
        descriptions = {
            1: "Executes immediately at current market price",
            2: "Executes only at specified price or better", 
            3: "Becomes market order when stop price is reached",
            4: "Becomes limit order when stop price is reached"
        }
        print(f"🎯 {name}: {descriptions[num]}")
    print("=" * 50)
    print("⚠️  WARNING: This will submit real orders to IBKR!")
    print("⚠️  Make sure you understand the risks before proceeding!")
    print("⚠️  Use paper trading account for testing!")

if __name__ == "__main__":
    show_order_info()
    
    # Safety confirmation
    print("\n🚨 IMPORTANT SAFETY CHECK 🚨")
    confirm = input("Are you using a PAPER TRADING account? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Please use paper trading account for testing!")
        print("❌ Exiting for safety...")
        sys.exit(1)
    
    main()