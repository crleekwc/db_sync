import socket
import json
import psycopg2
from psycopg2 import Error
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_sync_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_tcp_server(host: str = "localhost", port: int = 443) -> Optional[socket.socket]:
    """
    Create and start a TCP listening socket on the specified host and port.
    
    Parameters:
    - host (str): The host address to bind the server to. Defaults to env var SERVER_HOST or "localhost".
    - port (int): The port number to listen on. Defaults to env var SERVER_PORT or 443.
    
    Returns:
    - server_socket: The socket object if successful, None otherwise.
    """
    host = host if host != "localhost" else os.getenv("SERVER_HOST", "localhost")
    port = port if port != 443 else int(os.getenv("SERVER_PORT", 443))
    try:
        # Create a TCP/IP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Allow port reuse
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind the socket to the address
        server_socket.bind((host, port))
        
        # Listen for incoming connections (max 5 queued connections)
        server_socket.listen(5)
        logger.info(f"TCP server started on {host}:{port}, waiting for connections...")
        
        return server_socket
    except Exception as e:
        logger.error(f"Error starting TCP server on {host}:{port}: {e}")
        return None

def connect_to_postgres(dbname: str = None, user: str = None, password: str = None, host: str = "localhost", port: str = "5432") -> Optional[psycopg2.extensions.connection]:
    """
    Establish a connection to a PostgreSQL database using environment variables as defaults.
    
    Parameters:
    - dbname (str): The name of the database to connect to. Defaults to env var DB_NAME.
    - user (str): The username for the database. Defaults to env var DB_USER.
    - password (str): The password for the database. Defaults to env var DB_PASSWORD.
    - host (str): The host address of the database server. Defaults to env var DB_HOST or "localhost".
    - port (str): The port number of the database server. Defaults to env var DB_PORT or "5432".
    
    Returns:
    - connection: A connection object to the PostgreSQL database, or None if connection fails.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=dbname or os.getenv("DB_NAME"),
            user=user or os.getenv("DB_USER"),
            password=password or os.getenv("DB_PASSWORD"),
            host=host if host != "localhost" else os.getenv("DB_HOST", "localhost"),
            port=port if port != "5432" else os.getenv("DB_PORT", "5432")
        )
        logger.info("Successfully connected to the PostgreSQL database.")
        return connection
    except Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def insert_row(connection: psycopg2.extensions.connection, table_name: str, row_data: dict) -> bool:
    """
    Insert a row of data into a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to insert data into.
    - row_data (dict): A dictionary where keys are column names and values are the data to insert.
    
    Returns:
    - bool: True if the insertion was successful, False otherwise.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['%s'] * len(row_data))
        values = tuple(row_data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Successfully inserted row into table {table_name}.")
        return True
    except Error as e:
        logger.error(f"Error inserting row into table {table_name}: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def handle_client_data(client_socket: socket.socket, client_address: tuple, db_connection: psycopg2.extensions.connection, table_name: str) -> bool:
    """
    Receive data from a client over the TCP socket and insert it into the database.
    Handles data larger than buffer size by accumulating chunks until complete.
    
    Parameters:
    - client_socket: The socket object for the client connection.
    - client_address: The address of the connected client.
    - db_connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to insert data into.
    
    Returns:
    - bool: True if data was received and processed, False if the connection was closed or an error occurred.
    """
    try:
        buffer_size = int(os.getenv("BUFFER_SIZE", 4096))
        full_data = b""
        while True:
            chunk = client_socket.recv(buffer_size)
            if not chunk:
                logger.info(f"Client {client_address} disconnected.")
                return False
            full_data += chunk
            try:
                # Try to decode and parse JSON to check if complete
                decoded_data = full_data.decode('utf-8')
                json.loads(decoded_data)
                # If JSON parsing succeeds, process the data
                logger.info(f"Received complete data from {client_address}: {decoded_data[:100]}... (total {len(decoded_data)} characters)")
                rows = json.loads(decoded_data)
                # Insert each row into the database
                for row in rows:
                    # Assuming row is a list/tuple, convert to dict with assumed column names
                    # Adjust column names based on your table structure
                    row_dict = {
                        "column1": row[0] if len(row) > 0 else None,
                        "column2": row[1] if len(row) > 1 else None,
                        # Add more columns as needed based on table structure
                    }
                    insert_row(db_connection, table_name, row_dict)
                return True
            except json.JSONDecodeError:
                # Incomplete JSON, continue receiving
                continue
            except UnicodeDecodeError:
                # Incomplete UTF-8 sequence, continue receiving
                continue
    except Exception as e:
        logger.error(f"Error receiving data from {client_address}: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Connect to the PostgreSQL database on Host B using environment variables or defaults
    db_conn = connect_to_postgres(host=os.getenv("TARGET_DB_HOST", "localhost"))
    
    if db_conn:
        server = start_tcp_server()
        if server:
            try:
                while True:
                    # Wait for a connection
                    client_socket, client_address = server.accept()
                    logger.info(f"Connection established with {client_address}")
                    # Handle client data
                    table_name = os.getenv("TABLE_NAME", "your_table_name")
                    while handle_client_data(client_socket, client_address, db_conn, table_name):
                        pass  # Continue receiving data until connection closes or error occurs
                    client_socket.close()
            except KeyboardInterrupt:
                logger.info("\nShutting down TCP server...")
                server.close()
                db_conn.close()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.error(f"Server error: {e}")
                server.close()
                db_conn.close()
                logger.info("Database connection closed.")
    else:
        logger.error("Failed to connect to the database on Host B.")
