# Contents of /ibkr-connection/ibkr-connection/src/connect.py

from .ibapi_client import IBApi
import threading
import time
import uuid

def connect_to_ib(host, port, client_id):
    """
    Connect to Interactive Brokers TWS or Gateway
    
    Parameters:
    host: IP address (default: 127.0.0.1 for localhost)
    port: Port number (7497 for TWS, 4002 for Gateway)
    client_id: Unique client identifier
    """
    app = IBApi()
    
    try:
        print(f"Connecting to IBKR at {host}:{port} with client ID {client_id}")
        app.connect(host, port, client_id)
        
        # Start the socket in a thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        print(f"Function called — ID: {uuid.uuid4()}")
        
        # Wait for connection
        time.sleep(2)
        
        if app.isConnected():
            print("✅ Successfully connected to IBKR!")
            return app
        else:
            print("❌ Failed to connect to IBKR")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None