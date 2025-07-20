# Utility functions for IBKR connection

def log_message(message):
    """Logs a message to the console with a timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")

def format_account_summary(account_summary):
    """Formats the account summary for better readability."""
    formatted_summary = "\n".join([f"{key}: {value}" for key, value in account_summary.items()])
    return formatted_summary

def validate_connection_params(host, port, client_id):
    """Validates the connection parameters for IBKR."""
    if not isinstance(host, str):
        raise ValueError("Host must be a string.")
    if not isinstance(port, int) or port <= 0:
        raise ValueError("Port must be a positive integer.")
    if not isinstance(client_id, int) or client_id < 0:
        raise ValueError("Client ID must be a non-negative integer.")