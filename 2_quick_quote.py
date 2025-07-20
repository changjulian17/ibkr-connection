#!/usr/bin/env python3
"""
Quick Quote Utility - Get quotes quickly for forex using ib_insync

Shows all G10 currency pairs in a table, then allows selection for detailed quotes.
"""

import sys
from ib_insync import IB, Forex

def get_all_g10_quotes(ib):
    """Get quotes for all G10 currency pairs and display in table"""
    g10_pairs = [
        # Major USD pairs first (faster)
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD",
        # Cross pairs last (slower)
        "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    print("\n💱 Getting quotes for all G10 currency pairs...")
    print("⏳ This may take a moment...")
    
    quotes = {}
    
    for pair in g10_pairs:
        try:
            contract = Forex(pair)
            ib.qualifyContracts(contract)
            ticker = ib.reqMktData(contract, '', False, False)
            ib.sleep(1)  # Shorter wait for bulk quotes
            quotes[pair] = ticker
        except Exception as e:
            print(f"❌ Error getting quote for {pair}: {e}")
            quotes[pair] = None
    
    # Display table
    print("\n" + "="*80)
    print("📊 G10 CURRENCY PAIRS - LIVE QUOTES")
    print("="*80)
    print(f"{'Pair':<8} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Close':<10} {'Spread':<8}")
    print("-"*80)
    
    for pair in g10_pairs:
        ticker = quotes.get(pair)
        if ticker:
            bid = ticker.bid if ticker.bid and ticker.bid > 0 else 0
            ask = ticker.ask if ticker.ask and ticker.ask > 0 else 0
            last = ticker.last if ticker.last and str(ticker.last).lower() != 'nan' else 0
            close = ticker.close if ticker.close and str(ticker.close).lower() != 'nan' else 0
            spread = ask - bid if bid > 0 and ask > 0 else 0
            
            print(f"{pair:<8} {bid:<10.5f} {ask:<10.5f} {last:<10.5f} {close:<10.5f} {spread:<8.5f}")
        else:
            print(f"{pair:<8} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<8}")
    
    print("="*80)
    return quotes

def get_detailed_quote(ib, symbol):
    """Get detailed quote for a specific currency pair"""
    try:
        contract = Forex(symbol)
        ib.qualifyContracts(contract)
        ticker = ib.reqMktData(contract, '', False, False)
        ib.sleep(3)  # Longer wait for detailed quote

        # Display formatted quote
        print(f"\n📈 Detailed Quote for {symbol}:")
        print("=" * 40)
        
        if ticker.bid is not None and ticker.bid > 0:
            print(f"Bid:    {ticker.bid:.5f}")
        if ticker.ask is not None and ticker.ask > 0:
            print(f"Ask:    {ticker.ask:.5f}")
        if ticker.last is not None and not str(ticker.last).lower() == 'nan':
            print(f"Last:   {ticker.last:.5f}")
        if ticker.close is not None and not str(ticker.close).lower() == 'nan':
            print(f"Close:  {ticker.close:.5f}")
        
        if (ticker.bid is not None and ticker.bid > 0 and 
            ticker.ask is not None and ticker.ask > 0):
            spread = ticker.ask - ticker.bid
            mid = (ticker.bid + ticker.ask) / 2
            spread_pct = (spread / mid) * 100 if mid > 0 else 0
            print(f"Mid:    {mid:.5f}")
            print(f"Spread: {spread:.5f} ({spread_pct:.3f}%)")
        
        # Calculate daily change if we have both last and close
        if (ticker.last and ticker.close and 
            str(ticker.last).lower() != 'nan' and 
            str(ticker.close).lower() != 'nan' and
            ticker.close > 0):
            change = ticker.last - ticker.close
            change_pct = (change / ticker.close) * 100
            print(f"Change: {change:+.5f} ({change_pct:+.3f}%)")
        
        print("=" * 40)

        # Print full ticker object
        print(f"\n🔍 Full Ticker Object:")
        print("-" * 50)
        print(ticker)

    except Exception as e:
        print(f"❌ Error getting detailed quote for {symbol}: {e}")

def get_symbol_choice():
    """Ask user which symbol to get detailed quote for"""
    g10_pairs = [
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD",
        "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    print("\n💱 Select currency pair for detailed quote:")
    print("=" * 40)
    
    for i, pair in enumerate(g10_pairs, 1):
        print(f"{i:2d}. {pair}")
    print("12. Enter custom forex pair")
    print(" 0. Skip detailed quote")
    
    while True:
        try:
            choice = int(input("\nEnter choice (0-12): ").strip())
            if choice == 0:
                return None
            elif 1 <= choice <= 11:
                return g10_pairs[choice - 1]
            elif choice == 12:
                while True:
                    symbol = input("Enter forex pair (e.g., USDSGD): ").strip().upper()
                    if len(symbol) == 6:
                        return symbol
                    else:
                        print("❌ Forex symbol should be 6 characters")
            else:
                print("❌ Please enter a number between 0-12")
        except ValueError:
            print("❌ Please enter a valid number")

def main():
    host = "127.0.0.1"
    port = 7497
    client_id = 4

    print("🚀 G10 Forex Quote Table (ib_insync)")
    print("=" * 50)

    # Connect to IBKR
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id)
        print("✅ Connected to IBKR!")
    except Exception as e:
        print(f"❌ Failed to connect to IBKR: {e}")
        return

    try:
        # Get and display all G10 quotes in table
        quotes = get_all_g10_quotes(ib)
        
        # Ask if user wants detailed quote for any pair
        symbol = get_symbol_choice()
        if symbol:
            get_detailed_quote(ib, symbol)
        else:
            print("📋 Skipping detailed quote")

    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        ib.disconnect()
        print("\n📴 Disconnected from IBKR")

def show_forex_info():
    """Show forex trading information"""
    print("\n📚 G10 Currency Information:")
    print("=" * 50)
    print("🇺🇸 USD - US Dollar")
    print("🇪🇺 EUR - Euro")
    print("🇯🇵 JPY - Japanese Yen")
    print("🇬🇧 GBP - British Pound")
    print("🇨🇭 CHF - Swiss Franc")
    print("🇦🇺 AUD - Australian Dollar")
    print("🇨🇦 CAD - Canadian Dollar")
    print("🇳🇿 NZD - New Zealand Dollar")
    print("🇸🇬 SGD - Singapore Dollar")
    print("=" * 50)
    print("💡 Forex markets trade 24/5 (Sunday 5PM - Friday 5PM EST)")
    print("💡 Major pairs typically have tighter spreads")

if __name__ == "__main__":
    show_forex_info()
    print("\n")
    main()
    
    # Ask if user wants to run again
    while True:
        again = input("\n🔄 Run forex quotes again? (y/n): ").strip().lower()
        if again in ['y', 'yes']:
            main()
        elif again in ['n', 'no']:
            print("👋 Goodbye!")
            break
        else:
            print("❌ Please enter y or n")
