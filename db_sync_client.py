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
        logging.FileHandler("db_sync_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_to_tcp_server(host: str = "localhost", port: int = 443) -> Optional[socket.socket]:
    """
    Connect to a listening TCP socket on the specified host and port.
    
    Parameters:
    - host (str): The host address of the server to connect to. Defaults to env var SERVER_HOST or "localhost".
    - port (int): The port number of the server to connect to. Defaults to env var SERVER_PORT or 443.
    
    Returns:
    - client_socket: The socket object if connection is successful, None otherwise.
    """
    host = host if host != "localhost" else os.getenv("SERVER_HOST", "localhost")
    port = port if port != 443 else int(os.getenv("SERVER_PORT", 443))
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the server
        client_socket.connect((host, port))
        logger.info(f"Successfully connected to TCP server at {host}:{port}")
        return client_socket
    except Exception as e:
        logger.error(f"Error connecting to TCP server at {host}:{port}: {e}")
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

def query_table(connection: psycopg2.extensions.connection, table_name: str) -> list:
    """
    Query all information from a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query.
    
    Returns:
    - list: A list of tuples containing the rows of data from the table.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Successfully retrieved {len(rows)} rows from table {table_name}.")
        return rows
    except Error as e:
        logger.error(f"Error querying table {table_name}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def send_data_over_socket(client_socket: socket.socket, data: list) -> bool:
    """
    Send data over the socket connection as a JSON string.
    Ensures all data is sent even if it exceeds buffer size.
    
    Parameters:
    - client_socket: The socket object for the client connection.
    - data: The data to send (should be serializable to JSON).
    
    Returns:
    - bool: True if the data was sent successfully, False otherwise.
    """
    try:
        message = json.dumps(data)
        encoded_message = message.encode('utf-8')
        total_sent = 0
        while total_sent < len(encoded_message):
            sent = client_socket.send(encoded_message[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent
        logger.info(f"Sent data over socket: {message[:100]}... (total {len(message)} characters)")
        return True
    except Exception as e:
        logger.error(f"Error sending data over socket: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Connect to the PostgreSQL database on Host A using environment variables or defaults
    db_conn = connect_to_postgres(host=os.getenv("SOURCE_DB_HOST", "host_a_ip_address"))
    
    if db_conn:
        try:
            # Query data from the table
            table_name = os.getenv("TABLE_NAME", "your_table_name")
            table_data = query_table(db_conn, table_name)
            db_conn.close()
            logger.info("Database connection closed.")
            
            # Connect to the TCP server on Host B using environment variables or defaults
            client = connect_to_tcp_server(host=os.getenv("TARGET_SERVER_HOST", "host_b_ip_address"))
            if client:
                try:
                    # Send the queried data over the socket
                    if send_data_over_socket(client, table_data):
                        logger.info("Data sent successfully.")
                    else:
                        logger.warning("Failed to send data.")
                    client.close()
                    logger.info("Socket connection closed.")
                except Exception as e:
                    logger.error(f"Client error: {e}")
                    client.close()
        except Exception as e:
            logger.error(f"Database operation error: {e}")
            if db_conn:
                db_conn.close()
                logger.info("Database connection closed.")
    else:
        logger.error("Failed to connect to the database on Host A.")
