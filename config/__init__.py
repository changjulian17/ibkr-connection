"""Configuration package for IBKR trading application"""

from .settings import (
    # Connection settings
    DEFAULT_HOST,
    PAPER_TRADING_PORT,
    LIVE_TRADING_PORT,
    DEFAULT_CLIENT_ID,
    
    # File paths
    ORDER_HISTORY_FILE,
    LOGS_DIR,
    
    # Trading defaults
    DEFAULT_QUANTITIES,
    ORDER_TYPES,
    DEFAULT_EXCHANGES,
    DEFAULT_CURRENCIES,
    
    # Display settings
    DEFAULT_CURRENCY,
    TABLE_WIDTH,
    KEY_ACCOUNT_METRICS,
    
    # Risk management
    MAX_ORDER_VALUE,
    MAX_POSITION_SIZE,
)

__version__ = "1.0.0"
