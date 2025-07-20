#!/usr/bin/env python3
"""
Account Summary using ib_insync - Much simpler than raw IB API

This script demonstrates how to:
1. Get account summary information
2. Get current positions
3. Display account value and buying power
4. Show portfolio positions
5. Show open orders and order history

Make sure TWS or IB Gateway is running.
"""

from ib_insync import IB
import pandas as pd

def main():
    host = "127.0.0.1"
    port = 7497
    client_id = 5

    print("📊 IBKR Account Summary (ib_insync)...")

    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id)
        print("✅ Connected to IBKR!")
    except Exception as e:
        print(f"❌ Failed to connect to IBKR: {e}")
        return

    # Get account summary
    print("\n📋 Getting account summary...")
    account_values = ib.accountValues()
    
    if account_values:
        print("\n" + "="*60)
        print("📊 ACCOUNT SUMMARY")
        print("="*60)
        
        # Key metrics to display
        key_metrics = [
            'TotalCashValue',
            'NetLiquidation', 
            'BuyingPower',
            'AvailableFunds',
            'GrossPositionValue',
            'UnrealizedPnL',
            'RealizedPnL'
        ]
        
        for metric in key_metrics:
            for av in account_values:
                if av.tag == metric and av.currency == 'USD':
                    print(f"{metric:20}: ${float(av.value):>15,.2f}")
        print("="*60)
    else:
        print("❌ No account summary data received")

    # Get positions
    print("\n📈 Getting positions...")
    positions = ib.positions()
    
    if positions:
        print("\n" + "="*80)
        print("📈 CURRENT POSITIONS")
        print("="*80)
        print(f"{'Symbol':<10} {'Position':<10} {'Avg Cost':<12} {'Market Value':<15} {'UnrealPnL':<12}")
        print("-"*80)
        
        for pos in positions:
            symbol = pos.contract.symbol
            position = pos.position
            avg_cost = pos.avgCost
            market_value = position * avg_cost
            unrealized_pnl = pos.unrealizedPNL if pos.unrealizedPNL else 0
            
            print(f"{symbol:<10} {position:<10.0f} ${avg_cost:<11.2f} ${market_value:<14.2f} ${unrealized_pnl:<11.2f}")
        print("="*80)
    else:
        print("❌ No positions found")

    # Get open orders
    print("\n📋 Getting open orders...")
    open_orders = ib.openOrders()
    
    if open_orders:
        print("\n" + "="*90)
        print("📋 OPEN ORDERS")
        print("="*90)
        print(f"{'Order ID':<10} {'Symbol':<10} {'Action':<6} {'Quantity':<10} {'Type':<10} {'Price':<10} {'Status':<12}")
        print("-"*90)
        
        for order in open_orders:
            order_id = order.order.orderId
            symbol = order.contract.symbol
            action = order.order.action
            quantity = order.order.totalQuantity
            order_type = order.order.orderType
            price = order.order.lmtPrice if order.order.lmtPrice else order.order.auxPrice
            status = order.orderStatus.status
            
            print(f"{order_id:<10} {symbol:<10} {action:<6} {quantity:<10.0f} {order_type:<10} ${price:<9.2f} {status:<12}")
        print("="*90)
    else:
        print("❌ No open orders found")

    # Get recent trades/executions
    print("\n🔄 Getting recent trades...")
    trades = ib.trades()
    
    if trades:
        print("\n" + "="*100)
        print("🔄 RECENT TRADES")
        print("="*100)
        print(f"{'Order ID':<10} {'Symbol':<10} {'Action':<6} {'Quantity':<10} {'Status':<12} {'Filled':<10} {'Remaining':<10}")
        print("-"*100)
        
        for trade in trades[-10:]:  # Show last 10 trades
            order_id = trade.order.orderId
            symbol = trade.contract.symbol
            action = trade.order.action
            quantity = trade.order.totalQuantity
            status = trade.orderStatus.status
            filled = trade.orderStatus.filled
            remaining = trade.orderStatus.remaining
            
            print(f"{order_id:<10} {symbol:<10} {action:<6} {quantity:<10.0f} {status:<12} {filled:<10.0f} {remaining:<10.0f}")
        print("="*100)
    else:
        print("❌ No trades found")

    # Get portfolio items (more detailed than positions)
    print("\n💼 Getting portfolio details...")
    portfolio = ib.portfolio()
    
    if portfolio:
        print(f"\n📊 Portfolio has {len(portfolio)} items")
        total_value = sum(item.marketValue for item in portfolio if item.marketValue)
        total_unrealized = sum(item.unrealizedPNL for item in portfolio if item.unrealizedPNL)
        print(f"💰 Total Portfolio Value: ${total_value:,.2f}")
        print(f"📈 Total Unrealized P&L: ${total_unrealized:,.2f}")

    # Summary statistics
    print("\n📊 SUMMARY STATISTICS")
    print("="*50)
    print(f"🔢 Total Positions: {len(positions)}")
    print(f"📋 Open Orders: {len(open_orders)}")
    print(f"🔄 Total Trades: {len(trades)}")
    print("="*50)

    ib.disconnect()
    print("\n📴 Disconnected from IBKR")
    print("✅ Account summary completed")

def show_account_info():
    """Display information about account data"""
    print("📚 Account Data Information:")
    print("=" * 50)
    print("🔹 TotalCashValue: Available cash in account")
    print("🔹 NetLiquidation: Total account value")
    print("🔹 BuyingPower: Available buying power")
    print("🔹 AvailableFunds: Funds available for trading")
    print("🔹 GrossPositionValue: Total value of all positions")
    print("🔹 UnrealizedPnL: Unrealized profit/loss")
    print("🔹 RealizedPnL: Realized profit/loss")
    print("\n📋 Order Information:")
    print("🔹 Open Orders: Currently active orders")
    print("🔹 Recent Trades: Order history and execution status")
    print("🔹 Order Status: Submitted, Filled, Cancelled, etc.")
    print("=" * 50)

if __name__ == "__main__":
    show_account_info()
    print("\n")

    main()