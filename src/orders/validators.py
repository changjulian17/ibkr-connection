"""Order validation utilities"""

import re
from config.settings import MAX_ORDER_VALUE, MAX_POSITION_SIZE

def validate_symbol(symbol, instrument_type='forex'):
    """Validate trading symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False, "Symbol must be a non-empty string"
    
    symbol = symbol.upper().strip()
    
    if instrument_type == 'forex':
        if len(symbol) != 6:
            return False, "Forex symbols must be exactly 6 characters (e.g., EURUSD)"
        if not symbol.isalpha():
            return False, "Forex symbols must contain only letters"
    
    elif instrument_type == 'stock':
        if len(symbol) < 1 or len(symbol) > 5:
            return False, "Stock symbols must be 1-5 characters"
        if not re.match(r'^[A-Z]+$', symbol):
            return False, "Stock symbols must contain only uppercase letters"
    
    elif instrument_type == 'option':
        if len(symbol) < 1 or len(symbol) > 5:
            return False, "Option underlying symbols must be 1-5 characters"
    
    return True, "Valid symbol"

def validate_quantity(quantity, instrument_type='forex'):
    """Validate order quantity"""
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a number"
    
    if qty <= 0:
        return False, "Quantity must be positive"
    
    if qty > MAX_POSITION_SIZE:
        return False, f"Quantity exceeds maximum position size of {MAX_POSITION_SIZE:,}"
    
    # Instrument-specific validations
    if instrument_type == 'forex':
        if qty < 1000:
            return False, "Forex minimum quantity is 1,000"
        if qty > 10000000:  # 10M
            return False, "Forex maximum quantity is 10,000,000"
    
    elif instrument_type == 'stock':
        if qty != int(qty):
            return False, "Stock quantity must be a whole number"
        if qty < 1:
            return False, "Stock minimum quantity is 1"
    
    elif instrument_type == 'option':
        if qty != int(qty):
            return False, "Option quantity must be a whole number"
        if qty < 1:
            return False, "Option minimum quantity is 1"
    
    return True, "Valid quantity"

def validate_price(price, price_type='limit'):
    """Validate order price"""
    try:
        price_val = float(price)
    except (ValueError, TypeError):
        return False, f"{price_type.title()} price must be a number"
    
    if price_val <= 0:
        return False, f"{price_type.title()} price must be positive"
    
    if price_val > 1000000:  # 1M per unit
        return False, f"{price_type.title()} price seems unreasonably high"
    
    return True, "Valid price"

def validate_order_value(quantity, price, symbol):
    """Validate total order value"""
    try:
        total_value = float(quantity) * float(price)
    except (ValueError, TypeError):
        return False, "Cannot calculate order value"
    
    if total_value > MAX_ORDER_VALUE:
        return False, f"Order value ${total_value:,.2f} exceeds limit of ${MAX_ORDER_VALUE:,.2f}"
    
    return True, f"Order value: ${total_value:,.2f}"

def validate_forex_pair(symbol):
    """Validate forex pair format and check if it's a common pair"""
    valid, message = validate_symbol(symbol, 'forex')
    if not valid:
        return valid, message
    
    # Common forex pairs
    major_pairs = [
        'EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF', 'AUDUSD', 
        'USDCAD', 'NZDUSD', 'USDSGD'
    ]
    
    cross_pairs = [
        'EURGBP', 'EURJPY', 'GBPJPY', 'EURCHF', 'GBPCHF',
        'EURAUD', 'GBPAUD', 'AUDCHF', 'AUDJPY', 'CHFJPY'
    ]
    
    if symbol in major_pairs:
        return True, f"Major currency pair: {symbol}"
    elif symbol in cross_pairs:
        return True, f"Cross currency pair: {symbol}"
    else:
        return True, f"Exotic/custom currency pair: {symbol} (verify availability)"

def validate_order_parameters(symbol, action, quantity, order_type, 
                            limit_price=None, stop_price=None, 
                            instrument_type='forex'):
    """Comprehensive order parameter validation"""
    errors = []
    warnings = []
    
    # Validate symbol
    valid, msg = validate_symbol(symbol, instrument_type)
    if not valid:
        errors.append(f"Symbol: {msg}")
    
    # Validate action
    if action not in ['BUY', 'SELL']:
        errors.append("Action must be 'BUY' or 'SELL'")
    
    # Validate quantity
    valid, msg = validate_quantity(quantity, instrument_type)
    if not valid:
        errors.append(f"Quantity: {msg}")
    
    # Validate order type
    if order_type not in [1, 2, 3, 4]:
        errors.append("Order type must be 1 (Market), 2 (Limit), 3 (Stop), or 4 (Stop Limit)")
    
    # Validate prices based on order type
    if order_type in [2, 4] and limit_price is not None:  # Limit orders
        valid, msg = validate_price(limit_price, 'limit')
        if not valid:
            errors.append(f"Limit price: {msg}")
    
    if order_type in [3, 4] and stop_price is not None:  # Stop orders
        valid, msg = validate_price(stop_price, 'stop')
        if not valid:
            errors.append(f"Stop price: {msg}")
    
    # Validate order value for limit orders
    if order_type == 2 and limit_price is not None:
        valid, msg = validate_order_value(quantity, limit_price, symbol)
        if not valid:
            errors.append(f"Order value: {msg}")
        elif "exceeds" not in msg:
            warnings.append(msg)
    
    # Logical validations
    if order_type == 4 and limit_price is not None and stop_price is not None:
        if action == 'BUY' and limit_price <= stop_price:
            errors.append("For BUY stop-limit orders, limit price must be higher than stop price")
        elif action == 'SELL' and limit_price >= stop_price:
            errors.append("For SELL stop-limit orders, limit price must be lower than stop price")
    
    return errors, warnings

def is_market_hours():
    """Check if it's during market hours (simplified)"""
    # This is a placeholder - implement actual market hours logic
    import datetime
    now = datetime.datetime.now()
    
    # Very basic check - weekday during business hours
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        if 9 <= now.hour <= 17:  # 9 AM to 5 PM local time
            return True, "Market appears to be open"
    
    return False, "Market may be closed (simplified check)"