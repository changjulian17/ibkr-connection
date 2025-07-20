#!/usr/bin/env python3
"""
Market Data Example - Get quotes for forex, stocks, and options using ib_insync

This script demonstrates how to:
1. Get forex quotes (USDSGD)
2. (Stocks and options require market data subscriptions)

Make sure TWS or IB Gateway is running with market data subscriptions.
"""

from ib_insync import IB, Forex
from datetime import datetime, timedelta

def main():
    host = "127.0.0.1"
    port = 7497
    client_id = 3

    print("📊 IBKR Market Data Example Starting (ib_insync)...")

    ib = IB()
    ib.connect(host, port, clientId=client_id)

    # 1. Get USDSGD forex quote
    print("\n💱 Requesting USDSGD forex quote...")
    usdsgd_contract = Forex('USDSGD')
    ib.qualifyContracts(usdsgd_contract)
    usdsgd_ticker = ib.reqMktData(usdsgd_contract, '', False, False)
    ib.sleep(2)

    print("\n📋 Detailed Quote Information:")
    print("-" * 50)

    # USDSGD details
    if usdsgd_ticker.bid and usdsgd_ticker.ask:
        bid = usdsgd_ticker.bid
        ask = usdsgd_ticker.ask
        mid = (bid + ask) / 2
        spread = ask - bid
        print(f"💱 USDSGD: Bid={bid:.5f}, Ask={ask:.5f}, Mid={mid:.5f}, Spread={spread:.5f}")
    else:
        print("💱 USDSGD: No quote available")

    # Stocks and options require market data subscriptions
    print("\n📈 NVDA stock and NVDA call options quotes require market data subscriptions.")
    print("💡 Please ensure you have the appropriate subscriptions enabled in your IBKR account.")

    # Cancel market data subscriptions
    print("\n❌ Cancelling market data subscriptions...")
    ib.cancelMktData(usdsgd_ticker)

    ib.disconnect()
    print("📴 Disconnected from IBKR")
    print("✅ Market data example completed")

def show_market_data_info():
    print("📚 Market Data Information:")
    print("=" * 50)
    print("🔹 Forex (USDSGD): Usually free real-time data")
    print("🔹 US Stocks (NVDA): Requires market data subscription")
    print("🔹 Options: Requires options data subscription")
    print("🔹 If you see 'No quote available', check your data subscriptions")
    print("🔹 Paper trading accounts get delayed data (15-20 minutes)")
    print("=" * 50)

if __name__ == "__main__":
    show_market_data_info()
    print("\n")
    response = input("Continue with market data requests? (y/n): ")
    if response.lower() in ['y', 'yes']:
        main()
    else:
        print("❌ Market data example cancelled")
