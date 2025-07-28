"""Order History Management"""

import json
import os
from datetime import datetime
from config.settings import ORDER_HISTORY_FILE, DEFAULT_HOST, PAPER_TRADING_PORT, DEFAULT_CLIENT_ID

def get_pending_orders_from_ibkr():
    """Get pending orders directly from IBKR account"""
    from ib_insync import IB
    
    ib = IB()
    try:
        ib.connect(DEFAULT_HOST, PAPER_TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
        
        # Get all open orders from IBKR
        trades = ib.openTrades()
        
        pending_orders = []
        for trade in trades:
            # Filter for truly pending orders
            if trade.orderStatus.status in ['PreSubmitted', 'Submitted', 'PendingSubmit', 'PendingCancel']:
                order_info = {
                    'trade': trade,  # Keep the trade object for cancellation
                    'order_id': trade.order.orderId,
                    'symbol': trade.contract.symbol,
                    'action': trade.order.action,
                    'quantity': trade.order.totalQuantity,
                    'order_type': trade.order.orderType,
                    'status': trade.orderStatus.status,
                    'filled': trade.orderStatus.filled,
                    'remaining': trade.orderStatus.remaining,
                    'avg_fill_price': trade.orderStatus.avgFillPrice
                }
                
                # Add contract specific info
                if hasattr(trade.contract, 'currency'):
                    order_info['currency'] = trade.contract.currency
                if hasattr(trade.contract, 'exchange'):
                    order_info['exchange'] = trade.contract.exchange
                
                # Add price info for limit/stop orders
                if hasattr(trade.order, 'lmtPrice') and trade.order.lmtPrice:
                    order_info['limit_price'] = trade.order.lmtPrice
                if hasattr(trade.order, 'auxPrice') and trade.order.auxPrice:
                    order_info['stop_price'] = trade.order.auxPrice
                
                pending_orders.append(order_info)
        
        return pending_orders
        
    except Exception as e:
        print(f"❌ Error getting pending orders from IBKR: {e}")
        return []
    finally:
        ib.disconnect()

def load_order_history():
    """Load order history from file"""
    if os.path.exists(ORDER_HISTORY_FILE):
        try:
            with open(ORDER_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading order history: {e}")
            return []
    return []

def save_order_to_history(order_data):
    """Save order to history file"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(ORDER_HISTORY_FILE), exist_ok=True)
    
    history = load_order_history()
    order_data['timestamp'] = datetime.now().isoformat()
    order_data['id'] = len(history) + 1
    history.append(order_data)
    
    try:
        with open(ORDER_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        print("💾 Order saved to history")
    except Exception as e:
        print(f"❌ Error saving order history: {e}")

def display_order_history():
    """Display saved order history"""
    history = load_order_history()
    if not history:
        print("📭 No order history found")
        return None
    
    print("\n📚 Order History:")
    print("=" * 100)
    print(f"{'ID':<3} {'Date':<12} {'Symbol':<10} {'Action':<4} {'Qty':<8} {'Type':<12} {'Status':<10} {'Instrument':<10}")
    print("-" * 100)
    
    for order in history[-20:]:  # Show last 20 orders
        date_str = order['timestamp'][:10]  # YYYY-MM-DD
        symbol = order.get('symbol', 'N/A')
        action = order.get('action', 'N/A')
        quantity = order.get('quantity', 0)
        order_type = order.get('order_type', 'N/A')
        status = order.get('status', 'N/A')
        instrument = order.get('instrument_type', 'N/A')
        
        print(f"{order['id']:<3} {date_str:<12} {symbol:<10} {action:<4} "
              f"{quantity:<8} {order_type:<12} {status:<10} {instrument:<10}")
    
    print("=" * 100)
    return history

def search_orders(symbol=None, instrument_type=None, action=None):
    """Search orders by criteria"""
    history = load_order_history()
    if not history:
        return []
    
    filtered = history
    
    if symbol:
        filtered = [o for o in filtered if o.get('symbol', '').upper() == symbol.upper()]
    if instrument_type:
        filtered = [o for o in filtered if o.get('instrument_type') == instrument_type]
    if action:
        filtered = [o for o in filtered if o.get('action', '').upper() == action.upper()]
    
    return filtered

def get_order_by_id(order_id):
    """Get specific order by ID"""
    history = load_order_history()
    return next((o for o in history if o['id'] == order_id), None)

def get_recent_orders(limit=10):
    """Get most recent orders"""
    history = load_order_history()
    return history[-limit:] if history else []

def get_order_statistics():
    """Get basic statistics about order history"""
    history = load_order_history()
    if not history:
        return {}
    
    stats = {
        'total_orders': len(history),
        'instruments': {},
        'actions': {'BUY': 0, 'SELL': 0},
        'statuses': {},
        'order_types': {}
    }
    
    for order in history:
        # Count by instrument type
        instrument = order.get('instrument_type', 'unknown')
        stats['instruments'][instrument] = stats['instruments'].get(instrument, 0) + 1
        
        # Count by action
        action = order.get('action', '').upper()
        if action in stats['actions']:
            stats['actions'][action] += 1
        
        # Count by status
        status = order.get('status', 'unknown')
        stats['statuses'][status] = stats['statuses'].get(status, 0) + 1
        
        # Count by order type
        order_type = order.get('order_type', 'unknown')
        stats['order_types'][order_type] = stats['order_types'].get(order_type, 0) + 1
    
    return stats

def update_order_status(order_history_id, new_status):
    """Update order status in history"""
    try:
        orders = load_order_history()
        for order in orders:
            if order['id'] == order_history_id:
                order['status'] = new_status
                order['updated_at'] = datetime.now().isoformat()
                break
        
        # Save updated history
        with open(ORDER_HISTORY_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
        return True
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False

def get_pending_orders():
    """Get all pending orders from history (legacy function - use get_pending_orders_from_ibkr for live data)"""
    try:
        orders = load_order_history()
        pending_statuses = ['SUBMITTED', 'PENDING', 'BRACKET_SUBMITTED', 'PreSubmitted', 'Submitted']
        return [order for order in orders if order.get('status') in pending_statuses]
    except Exception as e:
        print(f"Error loading pending orders: {e}")
        return []