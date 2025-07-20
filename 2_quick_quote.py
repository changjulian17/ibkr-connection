#!/usr/bin/env python3
"""
Quick Quote Utility - Get quotes quickly for forex using ib_insync

Shows all G10 currency pairs in a table using threading for faster quotes.
"""

import sys
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from ib_insync import IB, Forex

def get_single_quote(pair, host="127.0.0.1", port=7497, base_client_id=100):
    """Get quote for a single currency pair using its own connection with event loop"""
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    ib = IB()
    try:
        # Use unique client ID for each thread
        client_id = base_client_id + hash(pair) % 1000
        ib.connect(host, port, clientId=client_id)
        
        contract = Forex(pair)
        ib.qualifyContracts(contract)
        ticker = ib.reqMktData(contract, '', False, False)
        ib.sleep(5)  # Increased wait time for better data
        
        ib.disconnect()
        return pair, ticker
        
    except Exception as e:
        print(f"❌ Error getting quote for {pair}: {e}")
        try:
            if ib.isConnected():
                ib.disconnect()
        except:
            pass
        return pair, None
    finally:
        # Clean up the event loop
        try:
            loop.close()
        except:
            pass

def get_all_g10_quotes_threaded():
    """Get quotes for all G10 currency pairs using threading"""
    # Reorder pairs: cross pairs first (slower), then major USD pairs (faster)
    g10_pairs = [
        # Cross pairs first (slower - need more time)
        "EURGBP", "EURJPY", "GBPJPY",
        # Major USD pairs last (faster)
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD"
    ]
    
    # print("\n💱 Getting quotes for all G10 currency pairs (threaded)...")
    # print("⚡ Starting with cross pairs first for better data!")
    
    quotes = {}
    
    # Use ThreadPoolExecutor with fewer workers to avoid overwhelming IBKR
    with ThreadPoolExecutor(max_workers=11) as executor:
        # Submit all tasks
        future_to_pair = {
            executor.submit(get_single_quote, pair): pair 
            for pair in g10_pairs
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_pair):
            try:
                pair, ticker = future.result()
                quotes[pair] = ticker
                # print(f"✅ Got quote for {pair}")
            except Exception as e:
                print(f"❌ Error processing future: {e}")
    
    # Display table in original order for consistency
    display_order = [
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD",
        "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    # Display table
    print("\n" + "="*80)
    print("📊 G10 CURRENCY PAIRS - LIVE QUOTES (THREADED)")
    print("="*80)
    print(f"{'Pair':<8} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Close':<10} {'Spread':<8}")
    print("-"*80)
    
    for pair in display_order:
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

def get_all_g10_quotes_single_connection(ib):
    """Alternative: Get quotes using single connection (your original method)"""
    # Reorder pairs: cross pairs first (slower), then major USD pairs (faster)
    g10_pairs = [
        # Cross pairs first (slower - need more time)
        "EURGBP", "EURJPY", "GBPJPY",
        # Major USD pairs last (faster)
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD"
    ]
    
    # print("\n💱 Getting quotes for all G10 currency pairs (single connection)...")
    # print("⏳ Starting with cross pairs first for better data...")
    
    quotes = {}
    
    for pair in g10_pairs:
        try:
            contract = Forex(pair)
            ib.qualifyContracts(contract)
            ticker = ib.reqMktData(contract, '', False, False)
            
            # Longer wait for cross pairs
            if pair in ["EURGBP", "EURJPY", "GBPJPY"]:
                ib.sleep(2.5)  # Extra time for cross pairs
                print(f"✅ Got quote for {pair} (cross pair)")
            else:
                ib.sleep(1.5)  # Standard time for major pairs
                print(f"✅ Got quote for {pair}")
                
            quotes[pair] = ticker
        except Exception as e:
            print(f"❌ Error getting quote for {pair}: {e}")
            quotes[pair] = None
    
    # Additional wait for complete data
    print("⏳ Waiting for complete market data...")
    ib.sleep(3)
    
    # Display table in original order for consistency
    display_order = [
        "EURUSD", "USDJPY", "GBPUSD", "USDCHF", 
        "AUDUSD", "USDCAD", "NZDUSD", "USDSGD",
        "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    # Display table
    print("\n" + "="*80)
    print("📊 G10 CURRENCY PAIRS - LIVE QUOTES (SINGLE CONNECTION)")
    print("="*80)
    print(f"{'Pair':<8} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Close':<10} {'Spread':<8}")
    print("-"*80)
    
    for pair in display_order:
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
        ib.sleep(3)

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
        
        # Calculate daily change
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

def choose_method():
    """Let user choose between threaded or single connection method"""
    # print("\n🚀 Choose quote method:")
    # print("1. Threaded (Fast - multiple connections)")
    # print("2. Single connection (Slower but more reliable)")
    
    while True:
        try:
            choice = 1 # int(input("\nEnter choice (1-2): ").strip())
            if choice == 1:
                return "threaded"
            elif choice == 2:
                return "single"
            else:
                print("❌ Please enter 1 or 2")
        except ValueError:
            print("❌ Please enter a valid number")

def main():
    host = "127.0.0.1"
    port = 7497
    client_id = 4

    # print("🚀 G10 Forex Quote Table (ib_insync)")
    # print("=" * 50)

    # Choose method
    method = choose_method()
    
    try:
        if method == "threaded":
            # Use threaded approach (no main connection needed)
            start_time = time.time()
            quotes = get_all_g10_quotes_threaded()
            end_time = time.time()
            print(f"⚡ Threaded quotes completed in {end_time - start_time:.2f} seconds")
            
            # For detailed quote, create a new connection
            # symbol = get_symbol_choice()
            # if symbol:
            #     ib = IB()
            #     ib.connect(host, port, clientId=client_id)
            #     get_detailed_quote(ib, symbol)
            #     ib.disconnect()
        else:
            # Use single connection approach
            ib = IB()
            ib.connect(host, port, clientId=client_id)
            print("✅ Connected to IBKR!")
            
            start_time = time.time()
            quotes = get_all_g10_quotes_single_connection(ib)
            end_time = time.time()
            print(f"🐌 Single connection quotes completed in {end_time - start_time:.2f} seconds")
            
            # symbol = get_symbol_choice()
            # if symbol:
            #     get_detailed_quote(ib, symbol)
            
            ib.disconnect()

    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n📴 Disconnected from IBKR")

def show_forex_info():
    """Show forex trading information"""
    # print("\n📚 G10 Currency Information:")
    # print("=" * 50)
    # print("🇺🇸 USD - US Dollar")
    # print("🇪🇺 EUR - Euro") 
    # print("🇯🇵 JPY - Japanese Yen")
    # print("🇬🇧 GBP - British Pound")
    # print("🇨🇭 CHF - Swiss Franc")
    # print("🇦🇺 AUD - Australian Dollar")
    # print("🇨🇦 CAD - Canadian Dollar")
    # print("🇳🇿 NZD - New Zealand Dollar")
    # print("🇸🇬 SGD - Singapore Dollar")
    # print("=" * 50)
    # print("💡 Forex markets trade 24/5 (Sunday 5PM - Friday 5PM EST)")
    # print("💡 Threaded method is faster but uses more connections")

if __name__ == "__main__":
    show_forex_info()
    print("\n")
    main()
    
    # Ask if user wants to run again
    # while True:
    #     again = input("\n🔄 Run forex quotes again? (y/n): ").strip().lower()
    #     if again in ['y', 'yes']:
    #         main()
    #     elif again in ['n', 'no']:
    #         print("👋 Goodbye!")
    #         break
    #     else:
    #         print("❌ Please enter y or n")
