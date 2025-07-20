#!/usr/bin/env python3
"""
Quick Quote Utility - Get quotes quickly for any symbol using ib_insync

Usage:
    python quick_quote.py NVDA
    python quick_quote.py USDSGD --forex
    python quick_quote.py NVDA --option --strike 130 --expiry 20250919 --right C
"""

import sys
import argparse
from ib_insync import IB, Forex, Stock, Option

def main():
    parser = argparse.ArgumentParser(description='Get quick quotes from IBKR (ib_insync)')
    parser.add_argument('symbol', help='Symbol to get quote for')
    parser.add_argument('--forex', action='store_true', help='Treat as forex pair (e.g., USDSGD)')
    parser.add_argument('--option', action='store_true', help='Treat as option')
    parser.add_argument('--strike', type=float, help='Strike price for options')
    parser.add_argument('--expiry', help='Expiry date for options (YYYYMMDD)')
    parser.add_argument('--right', choices=['C', 'P'], help='Call (C) or Put (P) for options')
    parser.add_argument('--exchange', default='SMART', help='Exchange (default: SMART)')
    args = parser.parse_args()

    host = "127.0.0.1"
    port = 7497
    client_id = 4

    print(f"📊 Getting quote for {args.symbol}...")

    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id)
    except Exception as e:
        print(f"❌ Failed to connect to IBKR: {e}")
        return

    # Create contract
    contract = None
    if args.forex:
        if len(args.symbol) != 6:
            print("❌ Forex symbol should be 6 characters (e.g., USDSGD)")
            ib.disconnect()
            return
        contract = Forex(args.symbol)
    elif args.option:
        if not all([args.strike, args.expiry, args.right]):
            print("❌ Options require --strike, --expiry, and --right")
            ib.disconnect()
            return
        contract = Option(
            args.symbol, args.expiry, args.strike, args.right,
            args.exchange, tradingClass=args.symbol
        )
    else:
        contract = Stock(args.symbol, args.exchange, 'USD')

    ib.qualifyContracts(contract)
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(3)

    print(f"\n📈 Quote for {args.symbol}:")
    print("-" * 30)
    if ticker.bid is not None:
        print(f"Bid: {ticker.bid:.4f}")
    if ticker.ask is not None:
        print(f"Ask: {ticker.ask:.4f}")
    if ticker.last is not None:
        print(f"Last: {ticker.last:.4f}")
    if ticker.bid is not None and ticker.ask is not None:
        spread = ticker.ask - ticker.bid
        mid = (ticker.bid + ticker.ask) / 2
        print(f"Mid: {mid:.4f}")
        print(f"Spread: {spread:.4f}")
    if ticker.bid is None and ticker.ask is None and ticker.last is None:
        print("❌ No quote data received")

    ib.cancelMktData(ticker)
    ib.disconnect()

if __name__ == "__main__":
    main()
