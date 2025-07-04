import socket
import json
import psycopg2
from psycopg2 import Error
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

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
    Connect to a listening TCP socket on the specified host and port with TLS encryption.
    
    Parameters:
    - host (str): The host address of the server to connect to. Defaults to env var SERVER_HOST or "localhost".
    - port (int): The port number of the server to connect to. Defaults to env var SERVER_PORT or 443.
    
    Returns:
    - client_socket: The socket object if connection is successful, None otherwise.
    """
    import ssl
    
    host = host if host != "localhost" else os.getenv("SERVER_HOST", "localhost")
    port = port if port != 443 else int(os.getenv("SERVER_PORT", 443))
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Wrap the socket with SSL/TLS
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        cert_file = os.getenv("SERVER_CERT_FILE", "server.crt")
        context.load_verify_locations(cert_file)  # Trust the server's self-signed certificate
        client_socket = context.wrap_socket(client_socket, server_hostname=host)
        
        # Connect to the server
        client_socket.connect((host, port))
        logger.info(f"Successfully connected to secure TLS server at {host}:{port}")
        return client_socket
    except Exception as e:
        logger.error(f"Error connecting to secure TLS server at {host}:{port}: {e}")
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
            dbname=dbname or os.getenv("SOURCE_DB_NAME"),
            user=user or os.getenv("SOURCE_DB_USER"),
            password=password or os.getenv("SOURCE_DB_PASSWORD"),
            host=host if host != "localhost" else os.getenv("SOURCE_DB_HOST", "localhost"),
            port=port if port != "5432" else os.getenv("SOURCE_DB_PORT", "5432")
        )
        logger.info("Successfully connected to the PostgreSQL database.")
        return connection
    except Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def query_table_schema(connection: psycopg2.extensions.connection, table_name: str) -> list:
    """
    Query the schema of a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query schema for.
    
    Returns:
    - list: A list of dictionaries defining column names and types.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s;
        """
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()
        schema = [{'name': col[0], 'type': col[1].upper()} for col in columns]
        logger.info(f"Successfully retrieved schema for table {table_name}: {schema}")
        return schema
    except Error as e:
        logger.error(f"Error querying schema for table {table_name}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def query_table(connection: psycopg2.extensions.connection, table_name: str, last_sent_id: int = 0) -> dict:
    """
    Query information and schema from a specified table in the PostgreSQL database.
    Only retrieves rows with id greater than last_sent_id if provided.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query.
    - last_sent_id (int): The ID of the last sent row to filter new data.
    
    Returns:
    - dict: A dictionary containing the schema, data rows, and the new last sent ID from the table.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        # Query data
        if last_sent_id > 0:
            query = f"SELECT * FROM {table_name} WHERE id > %s ORDER BY id;"
            cursor.execute(query, (last_sent_id,))
        else:
            query = f"SELECT * FROM {table_name} ORDER BY id;"
            cursor.execute(query)
        rows = cursor.fetchall()
        new_last_sent_id = last_sent_id
        if rows:
            logger.info(f"Successfully retrieved {len(rows)} new rows from table {table_name}.")
            # Update last sent ID based on the last row
            new_last_sent_id = rows[-1][0] if rows[-1][0] is not None else last_sent_id
        else:
            logger.info(f"No new rows found in table {table_name} since last sync.")
        # Query schema only if it's the initial sync
        schema = query_table_schema(connection, table_name) if last_sent_id == 0 else []
        return {'schema': schema, 'data': rows, 'new_last_sent_id': new_last_sent_id}
    except Error as e:
        logger.error(f"Error querying table {table_name}: {e}")
        return {'schema': [], 'data': [], 'new_last_sent_id': last_sent_id}
    finally:
        if cursor:
            cursor.close()

def send_data_over_socket(client_socket: socket.socket, payload: dict) -> bool:
    """
    Send data over the socket connection as a JSON string.
    Ensures all data is sent even if it exceeds buffer size.
    
    Parameters:
    - client_socket: The socket object for the client connection.
    - payload: The payload containing schema and data to send (should be serializable to JSON).
    
    Returns:
    - bool: True if the data was sent successfully, False otherwise.
    """
    try:
        # Prepare payload without new_last_sent_id
        send_payload = {'schema': payload['schema'], 'data': payload['data']}
        message = json.dumps(send_payload)
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
    import time
    import pickle
    
    # File to store the last sent ID for persistence
    LAST_SENT_ID_FILE = "last_sent_id.pkl"
    
def load_last_sent_id():
    """Load the last sent ID from a file if it exists, initialize a new file if it doesn't."""
    try:
        if os.path.exists(LAST_SENT_ID_FILE):
            with open(LAST_SENT_ID_FILE, 'rb') as f:
                return pickle.load(f)
        else:
            # Initialize a new pickle file with ID 0 if it doesn't exist
            with open(LAST_SENT_ID_FILE, 'wb') as f:
                pickle.dump(0, f)
            logger.info(f"Initialized new last sent ID file: {LAST_SENT_ID_FILE}")
            return 0
    except Exception as e:
        logger.error(f"Error loading last sent ID: {e}")
        return 0
    
    def save_last_sent_id(last_sent_id):
        """Save the last sent ID to a file for persistence."""
        try:
            with open(LAST_SENT_ID_FILE, 'wb') as f:
                pickle.dump(last_sent_id, f)
        except Exception as e:
            logger.error(f"Error saving last sent ID: {e}")
    
    # Load the last sent ID from previous execution
    last_sent_id = load_last_sent_id()
    logger.info(f"Starting sync with last sent ID: {last_sent_id}")
    
    # Connect to the PostgreSQL database on Host A using environment variables or defaults
    db_conn = connect_to_postgres(host=os.getenv("SOURCE_DB_HOST", "host_a_ip_address"))
    
    if db_conn:
        try:
            table_name = os.getenv("TABLE_NAME", "your_table_name")
            sync_interval = int(os.getenv("SYNC_INTERVAL_SECONDS", 60))  # Default to 60 seconds
            
            while True:
                try:
                    # Query new data and schema (schema only on initial sync)
                    table_payload = query_table(db_conn, table_name, last_sent_id)
                    if table_payload['data'] or table_payload['schema']:  # Send if there is new data or initial schema
                        # Connect to the TCP server on Host B
                        client = connect_to_tcp_server(host=os.getenv("TARGET_SERVER_HOST", "host_b_ip_address"))
                        if client:
                            try:
                                if send_data_over_socket(client, table_payload):
                                    logger.info(f"New data sent successfully. Rows: {len(table_payload['data'])}")
                                    # Update last sent ID if there was new data
                                    if table_payload['data']:
                                        last_sent_id = table_payload['new_last_sent_id']
                                        save_last_sent_id(last_sent_id)
                                        logger.info(f"Updated last sent ID to: {last_sent_id}")
                                else:
                                    logger.warning("Failed to send data.")
                                client.close()
                                logger.info("Socket connection closed.")
                            except Exception as e:
                                logger.error(f"Client error: {e}")
                                client.close()
                    else:
                        logger.info("No new data to sync.")
                    
                    # Wait before the next sync
                    time.sleep(sync_interval)
                except KeyboardInterrupt:
                    logger.info("Stopping continuous sync...")
                    break
                except Exception as e:
                    logger.error(f"Sync loop error: {e}")
                    time.sleep(sync_interval)  # Wait before retrying on error
        except Exception as e:
            logger.error(f"Database operation error: {e}")
        finally:
            if db_conn:
                db_conn.close()
                logger.info("Database connection closed.")
    else:
        logger.error("Failed to connect to the database on Host A.")
