# Required imports
import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import TickerId

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}  # Store data
        self.contract_details = {}
        self.account_summary = {}  # Store account summary
        self.positions = {}  # Store positions
        self.account = None  # Store account number
        self.next_valid_order_id = None  # Initialize next valid order ID
        
    # Connection status callbacks
    def connectAck(self):
        print("Connection acknowledged")
        
    def connectionClosed(self):
        print("Connection closed")
        
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        print(f"Error {errorCode}: {errorString}")
        
    # Account information callback
    def managedAccounts(self, accountsList: str):
        print(f"Managed accounts: {accountsList}")
        self.account = accountsList.split(",")[0]  # Use first account
        
    # Position callback
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        print(f"Position - Account: {account}, Symbol: {contract.symbol}, "
              f"Position: {position}, Avg Cost: {avgCost}")
        
        # Store position data
        key = f"{account}_{contract.symbol}"
        self.positions[key] = {
            'account': account,
            'symbol': contract.symbol,
            'position': position,
            'avg_cost': avgCost,
            'contract': contract
        }
              
    def positionEnd(self):
        print("✅ Position data received completely")
        self.display_positions()
        print("Position data received completely")
        
    # Market data callbacks
    def tickPrice(self, reqId: TickerId, tickType, price: float, attrib):
        print(f"Tick Price - ID: {reqId}, Type: {tickType}, Price: {price}")
        
    def tickSize(self, reqId: TickerId, tickType, size: int):
        print(f"Tick Size - ID: {reqId}, Type: {tickType}, Size: {size}")

    # Account summary callbacks
    def accountSummary(self, reqId: TickerId, account: str, tag: str, value: str, currency: str):
        """Callback for account summary data"""
        key = f"{account}_{tag}_{currency}"
        self.account_summary[key] = {
            'account': account,
            'tag': tag,
            'value': value,
            'currency': currency
        }
        
    def accountSummaryEnd(self, reqId: TickerId):
        """Called when account summary is complete"""
        print("✅ Account summary received completely")
        self.display_account_summary()
        
    def nextValidId(self, orderId):
        print("✅ Confirmed connection with nextValidId")
        self.next_valid_order_id = orderId
        
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        """Callback for order status updates"""
        print(f"📋 Order Status - ID: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, Avg Fill Price: {avgFillPrice}")
        
    def openOrder(self, orderId, contract, order, orderState):
        """Callback for open orders"""
        print(f"📝 Open Order - ID: {orderId}, Symbol: {contract.symbol}, Action: {order.action}, Quantity: {order.totalQuantity}, Type: {order.orderType}")
        
    def execDetails(self, reqId, contract, execution):
        """Callback for execution details"""
        print(f"✅ Execution - Symbol: {contract.symbol}, Side: {execution.side}, Shares: {execution.shares}, Price: {execution.price}")
        
    def request_account_summary(self):
        """Request account summary information"""
        if hasattr(self, 'account') and self.account:
            print("📊 Requesting account summary...")
            # Request key account summary tags
            tags = "TotalCashValue,NetLiquidation,BuyingPower,AccruedCash,AvailableFunds"
            self.reqAccountSummary(9001, "All", tags)
        else:
            print("❌ No account available for summary request")
            
    def request_positions(self):
        """Request all positions"""
        print("📈 Requesting positions...")
        self.reqPositions()
        
    def display_account_summary(self):
        """Display formatted account summary"""
        if not self.account_summary:
            print("No account summary data available")
            return
            
        print("\n" + "="*50)
        print("📊 ACCOUNT SUMMARY")
        print("="*50)
        
        for key, data in self.account_summary.items():
            tag = data['tag']
            value = data['value']
            currency = data['currency']
            print(f"{tag:20}: {value:>15} {currency}")
        print("="*50)
        
    def display_positions(self):
        """Display formatted positions"""
        if not self.positions:
            print("No positions found")
            return
            
        print("\n" + "="*60)
        print("📈 PORTFOLIO POSITIONS")
        print("="*60)
        print(f"{'Symbol':<10} {'Position':<12} {'Avg Cost':<12} {'Market Value':<15}")
        print("-"*60)
        
        for key, pos in self.positions.items():
            symbol = pos['symbol']
            position = pos['position']
            avg_cost = pos['avg_cost']
            market_value = position * avg_cost if avg_cost else 0
            print(f"{symbol:<10} {position:<12.2f} {avg_cost:<12.2f} ${market_value:<14.2f}")
        print("="*60)
        
    def get_next_order_id(self):
        """Get the next valid order ID"""
        if hasattr(self, 'next_valid_order_id'):
            order_id = self.next_valid_order_id
            self.next_valid_order_id += 1
            return order_id
        else:
            print("❌ Next valid order ID not received yet")
            return None
            
    # Market Data Methods
    def create_forex_contract(self, base_currency, quote_currency, exchange="IDEALPRO"):
        """Create a forex contract"""
        contract = Contract()
        contract.symbol = base_currency
        contract.secType = "CASH"
        contract.currency = quote_currency
        contract.exchange = exchange
        return contract
    
    def create_stock_contract(self, symbol, exchange="SMART", currency="USD"):
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def create_option_contract(self, symbol, expiry, strike, right, exchange="SMART", currency="USD"):
        """
        Create an options contract
        
        Args:
            symbol: Underlying symbol (e.g., 'NVDA')
            expiry: Expiration date in YYYYMMDD format (e.g., '20240920')
            strike: Strike price (e.g., 120.0)
            right: 'C' for Call, 'P' for Put
            exchange: Exchange (default: 'SMART')
            currency: Currency (default: 'USD')
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "OPT"
        contract.exchange = exchange
        contract.currency = currency
        contract.lastTradeDateOrContractMonth = expiry
        contract.strike = strike
        contract.right = right
        contract.multiplier = "100"
        return contract
    
    def request_market_data(self, contract, generic_tick_list="", snapshot=False):
        """
        Request market data for a contract
        
        Args:
            contract: Contract object
            generic_tick_list: Additional tick types (optional)
            snapshot: True for snapshot, False for streaming
        """
        req_id = len(self.data) + 1000  # Use unique request ID
        
        # Store contract info for this request
        self.data[req_id] = {
            'contract': contract,
            'bid': None,
            'ask': None,
            'last': None,
            'volume': None,
            'timestamp': None
        }
        
        print(f"📊 Requesting market data for {contract.symbol} (ID: {req_id})")
        self.reqMktData(req_id, contract, generic_tick_list, snapshot, False, [])
        return req_id
    
    def cancel_market_data(self, req_id):
        """Cancel market data subscription"""
        self.cancelMktData(req_id)
        print(f"❌ Cancelled market data for request ID: {req_id}")
    
    # Enhanced market data callbacks
    def tickPrice(self, reqId: TickerId, tickType, price: float, attrib):
        """Enhanced tick price callback with better data storage"""
        if reqId in self.data:
            contract = self.data[reqId]['contract']
            
            # Tick types: 1=Bid, 2=Ask, 4=Last, 6=High, 7=Low, 9=Close
            if tickType == 1:  # Bid
                self.data[reqId]['bid'] = price
                print(f"💰 {contract.symbol} Bid: ${price}")
            elif tickType == 2:  # Ask
                self.data[reqId]['ask'] = price
                print(f"💰 {contract.symbol} Ask: ${price}")
            elif tickType == 4:  # Last
                self.data[reqId]['last'] = price
                print(f"💰 {contract.symbol} Last: ${price}")
            elif tickType == 6:  # High
                print(f"📈 {contract.symbol} High: ${price}")
            elif tickType == 7:  # Low
                print(f"📉 {contract.symbol} Low: ${price}")
            elif tickType == 9:  # Close
                print(f"🔒 {contract.symbol} Close: ${price}")
        
    def tickSize(self, reqId: TickerId, tickType, size: int):
        """Enhanced tick size callback"""
        if reqId in self.data:
            contract = self.data[reqId]['contract']
            
            # Tick types: 0=Bid Size, 3=Ask Size, 5=Last Size, 8=Volume
            if tickType == 0:  # Bid Size
                print(f"📊 {contract.symbol} Bid Size: {size}")
            elif tickType == 3:  # Ask Size
                print(f"📊 {contract.symbol} Ask Size: {size}")
            elif tickType == 5:  # Last Size
                print(f"📊 {contract.symbol} Last Size: {size}")
            elif tickType == 8:  # Volume
                self.data[reqId]['volume'] = size
                print(f"📊 {contract.symbol} Volume: {size}")
    
    def get_quote(self, req_id):
        """Get current quote for a request ID"""
        if req_id in self.data:
            return self.data[req_id]
        return None
    
    def display_quotes(self):
        """Display all current quotes"""
        if not self.data:
            print("No market data available")
            return
            
        print("\n" + "="*80)
        print("📈 CURRENT MARKET QUOTES")
        print("="*80)
        print(f"{'Symbol':<10} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Volume':<12} {'Spread':<10}")
        print("-"*80)
        
        for req_id, data in self.data.items():
            if 'contract' in data:
                contract = data['contract']
                symbol = contract.symbol
                bid = data['bid'] if data['bid'] else 0
                ask = data['ask'] if data['ask'] else 0
                last = data['last'] if data['last'] else 0
                volume = data['volume'] if data['volume'] else 0
                spread = ask - bid if bid and ask else 0
                
                print(f"{symbol:<10} {bid:<10.2f} {ask:<10.2f} {last:<10.2f} {volume:<12} {spread:<10.4f}")
        print("="*80)