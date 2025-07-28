"""Configuration settings for IBKR connection and trading application"""

# IBKR Connection Settings
DEFAULT_HOST = "127.0.0.1"
PAPER_TRADING_PORT = 7497
LIVE_TRADING_PORT = 7496
DEFAULT_CLIENT_ID = 5

# File Storage Settings
ORDER_HISTORY_FILE = "data/order_history.json"
LOGS_DIR = "data/logs"
TRADE_LOGS_DIR = "data/trade_logs"

# Trading Defaults
DEFAULT_QUANTITIES = {
    'forex': 10000,
    'stock': 100,
    'option': 1
}

# Risk Management
MAX_ORDER_VALUE = 50000  # Maximum order value in USD
MAX_POSITION_SIZE = 100000  # Maximum position size

# Timeouts and Retries
CONNECTION_TIMEOUT = 10
MARKET_DATA_TIMEOUT = 5
ORDER_SUBMISSION_TIMEOUT = 30
MAX_RETRIES = 3
SLEEP_INTERVAL = 1

# Display Settings
DEFAULT_CURRENCY = "USD"
DECIMAL_PLACES = 2
TABLE_WIDTH = 100

# Account Summary Key Metrics (what to display)
KEY_ACCOUNT_METRICS = [
    'TotalCashValue',
    'NetLiquidation', 
    'BuyingPower',
    'AvailableFunds',
    'GrossPositionValue',
    'UnrealizedPnL',
    'RealizedPnL'
]

# Order Types
ORDER_TYPES = {
    1: "Market Order",
    2: "Limit Order", 
    3: "Stop Order",
    4: "Stop Limit Order"
}

# Exchange Mappings
DEFAULT_EXCHANGES = {
    'stock': 'SMART',
    'option': 'SMART',
    'forex': 'IDEALPRO'
}

# Currencies
DEFAULT_CURRENCIES = {
    'stock': 'USD',
    'option': 'USD', 
    'forex': 'USD'
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "data/logs/trading.log"

# API Rate Limits
API_RATE_LIMIT = 50  # requests per second
MARKET_DATA_LINES = 3  # max simultaneous market data subscriptions