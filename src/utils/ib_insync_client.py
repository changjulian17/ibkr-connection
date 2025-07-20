#!/usr/bin/env python3
"""
IB_Insync Client - Simplified IBKR Interface using ib_insync

This provides a much cleaner and more pythonic interface to IBKR
compared to the raw ibapi.

Features:
- Automatic connection management
- Synchronous operations (no callbacks needed)
- Built-in pandas DataFrames support
- Much simpler contract creation
- Easier market data handling
"""

from ib_insync import *
import pandas as pd
from datetime import datetime, timedelta
import time

class IBInsyncClient:
    def __init__(self):
        """Initialize the ib_insync client"""
        self.ib = IB()
        self.connected = False
        
    def connect(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Connect to IBKR TWS or Gateway
        
        Args:
            host: IP address (default: 127.0.0.1)
            port: Port number (7497 for TWS, 4002 for Gateway)
            client_id: Unique client identifier
        """
        try:
            print(f"🔌 Connecting to IBKR at {host}:{port} with client ID {client_id}")
            self.ib.connect(host, port, clientId=client_id)
            self.connected = True
            print("✅ Connected to IBKR successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("📴 Disconnected from IBKR")
    
    def get_account_summary(self):
        """Get account summary as a pandas DataFrame"""
        if not self.connected:
            print("❌ Not connected to IBKR")
            return None
            
        try:
            print("📊 Getting account summary...")
            summary = self.ib.accountSummary()
            df = util.df(summary)
            print("✅ Account summary retrieved")
            return df
        except Exception as e:
            print(f"❌ Error getting account summary: {e}")
            return None
    
    def get_positions(self):
        """Get current positions as a pandas DataFrame"""
        if not self.connected:
            print("❌ Not connected to IBKR")
            return None
            
        try:
            print("📈 Getting positions...")
            positions = self.ib.positions()
            if positions:
                df = util.df(positions)
                print(f"✅ Found {len(positions)} positions")
                return df
            else:
                print("📭 No positions found")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
            return None
    
    def get_portfolio(self):
        """Get portfolio items as a pandas DataFrame"""
        if not self.connected:
            print("❌ Not connected to IBKR")
            return None
            
        try:
            print("💼 Getting portfolio...")
            portfolio = self.ib.portfolio()
            if portfolio:
                df = util.df(portfolio)
                print(f"✅ Found {len(portfolio)} portfolio items")
                return df
            else:
                print("📭 No portfolio items found")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error getting portfolio: {e}")
            return None
    
    def get_stock_quote(self, symbol, exchange='SMART', currency='USD'):
        """
        Get real-time quote for a stock
        
        Args:
            symbol: Stock symbol (e.g., 'NVDA')
            exchange: Exchange (default: 'SMART')
            currency: Currency (default: 'USD')
        """
        try:
            print(f"📈 Getting quote for {symbol}...")
            contract = Stock(symbol, exchange, currency)
            
            # Request market data
            self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data
            
            ticker = self.ib.ticker(contract)
            
            quote = {
                'symbol': symbol,
                'bid': ticker.bid if ticker.bid != -1 else None,
                'ask': ticker.ask if ticker.ask != -1 else None,
                'last': ticker.last if ticker.last != -1 else None,
                'close': ticker.close if ticker.close != -1 else None,
                'volume': ticker.volume if ticker.volume != -1 else None,
                'timestamp': datetime.now()
            }
            
            # Calculate additional fields
            if quote['bid'] and quote['ask']:
                quote['spread'] = quote['ask'] - quote['bid']
                quote['mid'] = (quote['bid'] + quote['ask']) / 2
            
            print(f"✅ Quote retrieved for {symbol}")
            return quote
            
        except Exception as e:
            print(f"❌ Error getting quote for {symbol}: {e}")
            return None
    
    def get_forex_quote(self, base_currency, quote_currency, exchange='IDEALPRO'):
        """
        Get real-time quote for forex pair
        
        Args:
            base_currency: Base currency (e.g., 'USD')
            quote_currency: Quote currency (e.g., 'SGD')
            exchange: Exchange (default: 'IDEALPRO')
        """
        try:
            symbol = f"{base_currency}{quote_currency}"
            print(f"💱 Getting forex quote for {symbol}...")
            
            contract = Forex(base_currency + quote_currency)
            
            # Request market data
            self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data
            
            ticker = self.ib.ticker(contract)
            
            quote = {
                'symbol': symbol,
                'bid': ticker.bid if ticker.bid != -1 else None,
                'ask': ticker.ask if ticker.ask != -1 else None,
                'last': ticker.last if ticker.last != -1 else None,
                'close': ticker.close if ticker.close != -1 else None,
                'timestamp': datetime.now()
            }
            
            # Calculate additional fields
            if quote['bid'] and quote['ask']:
                quote['spread'] = quote['ask'] - quote['bid']
                quote['mid'] = (quote['bid'] + quote['ask']) / 2
            
            print(f"✅ Forex quote retrieved for {symbol}")
            return quote
            
        except Exception as e:
            print(f"❌ Error getting forex quote: {e}")
            return None
    
    def get_option_quote(self, symbol, expiry, strike, right, exchange='SMART', currency='USD'):
        """
        Get real-time quote for an option
        
        Args:
            symbol: Underlying symbol (e.g., 'NVDA')
            expiry: Expiration date as string 'YYYYMMDD' (e.g., '20250919')
            strike: Strike price (e.g., 130.0)
            right: 'C' for Call, 'P' for Put
            exchange: Exchange (default: 'SMART')
            currency: Currency (default: 'USD')
        """
        try:
            print(f"📞 Getting option quote for {symbol} {expiry} ${strike} {right}...")
            
            contract = Option(symbol, expiry, strike, right, exchange, currency=currency)
            
            # Request market data
            self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(3)  # Wait longer for options data
            
            ticker = self.ib.ticker(contract)
            
            quote = {
                'symbol': f"{symbol}_{expiry}_{strike}_{right}",
                'underlying': symbol,
                'expiry': expiry,
                'strike': strike,
                'right': right,
                'bid': ticker.bid if ticker.bid != -1 else None,
                'ask': ticker.ask if ticker.ask != -1 else None,
                'last': ticker.last if ticker.last != -1 else None,
                'close': ticker.close if ticker.close != -1 else None,
                'volume': ticker.volume if ticker.volume != -1 else None,
                'timestamp': datetime.now()
            }
            
            # Calculate additional fields
            if quote['bid'] and quote['ask']:
                quote['spread'] = quote['ask'] - quote['bid']
                quote['mid'] = (quote['bid'] + quote['ask']) / 2
            
            print(f"✅ Option quote retrieved")
            return quote
            
        except Exception as e:
            print(f"❌ Error getting option quote: {e}")
            return None
    
    def get_option_chain(self, symbol, expiry_date=None, exchange='SMART'):
        """
        Get option chain for a symbol
        
        Args:
            symbol: Underlying symbol (e.g., 'NVDA')
            expiry_date: Specific expiry date or None for all
            exchange: Exchange (default: 'SMART')
        """
        try:
            print(f"🔗 Getting option chain for {symbol}...")
            
            # Get the underlying contract
            stock = Stock(symbol, exchange, 'USD')
            
            # Request option chain
            chains = self.ib.reqSecDefOptParams(stock.symbol, '', stock.secType, stock.conId)
            
            if not chains:
                print(f"❌ No option chains found for {symbol}")
                return None
            
            # Convert to DataFrame for easier handling
            chain_data = []
            for chain in chains:
                for expiry in chain.expirations:
                    for strike in chain.strikes:
                        if expiry_date is None or expiry == expiry_date:
                            chain_data.append({
                                'symbol': symbol,
                                'expiry': expiry,
                                'strike': strike,
                                'exchange': chain.exchange,
                                'multiplier': chain.multiplier
                            })
            
            df = pd.DataFrame(chain_data)
            print(f"✅ Found {len(df)} option contracts")
            return df
            
        except Exception as e:
            print(f"❌ Error getting option chain: {e}")
            return None
    
    def display_quote(self, quote):
        """Display a quote in a formatted way"""
        if not quote:
            print("❌ No quote to display")
            return
            
        print(f"\n📊 Quote for {quote['symbol']}")
        print("-" * 40)
        
        if quote.get('bid'):
            print(f"Bid:    ${quote['bid']:.4f}")
        if quote.get('ask'):
            print(f"Ask:    ${quote['ask']:.4f}")
        if quote.get('last'):
            print(f"Last:   ${quote['last']:.4f}")
        if quote.get('mid'):
            print(f"Mid:    ${quote['mid']:.4f}")
        if quote.get('spread'):
            print(f"Spread: ${quote['spread']:.4f}")
        if quote.get('volume'):
            print(f"Volume: {quote['volume']:,}")
        if quote.get('close'):
            print(f"Close:  ${quote['close']:.4f}")
            
        print(f"Time:   {quote['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 40)
    
    def get_september_expiry(self, year=2025):
        """Get the third Friday of September (typical options expiry)"""
        month = 9
        first_day = datetime(year, month, 1)
        
        # Find the first Friday (weekday 4 = Friday)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)
        
        # Third Friday is 14 days after first Friday
        third_friday = first_friday + timedelta(days=14)
        
        return third_friday.strftime("%Y%m%d")
