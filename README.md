# IBKR Connection Project

This project provides a Python interface to connect to Interactive Brokers (IBKR) using the IBAPI library. It includes classes and functions to manage connections, handle market data, and retrieve account information.

## Project Structure

```
ibkr-connection
├── src
│   ├── ibapi_client.py       # Defines the IBApi class for handling IBKR API interactions
│   ├── connect.py            # Contains the connect_to_ib function for establishing connections
│   └── utils.py              # Utility functions for logging and data formatting
├── requirements.txt          # Lists project dependencies
└── README.md                 # Documentation for the project
```

## Prerequisites

1. **Interactive Brokers Software**: Ensure that either Trader Workstation (TWS) or IB Gateway is running.
2. **API Settings**: Enable API connections in TWS/Gateway:
   - Navigate to `File > Global Configuration > API > Settings`
   - Check "Enable ActiveX and Socket Clients"
   - Note the Socket port (default: 7497 for TWS, 4002 for Gateway)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ibkr-connection
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start TWS or IB Gateway.
2. Run the connection script:
   ```python
   from src.connect import connect_to_ib

   app = connect_to_ib(host="127.0.0.1", port=7497, client_id=1)
   ```

3. Use the `IBApi` class methods to interact with the IBKR API.

## License

This project is licensed under the MIT License. See the LICENSE file for details.