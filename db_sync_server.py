import socket
import json
import psycopg2
from psycopg2 import Error

def start_tcp_server(host="localhost", port=443):
    """
    Create and start a TCP listening socket on the specified host and port.
    
    Parameters:
    - host (str): The host address to bind the server to (default: localhost).
    - port (int): The port number to listen on (default: 443).
    
    Returns:
    - server_socket: The socket object if successful, None otherwise.
    """
    try:
        # Create a TCP/IP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Allow port reuse
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind the socket to the address
        server_socket.bind((host, port))
        
        # Listen for incoming connections (max 5 queued connections)
        server_socket.listen(5)
        print(f"TCP server started on {host}:{port}, waiting for connections...")
        
        return server_socket
    except Exception as e:
        print(f"Error starting TCP server on {host}:{port}: {e}")
        return None

def connect_to_postgres(dbname, user, password, host="localhost", port="5432"):
    """
    Establish a connection to a PostgreSQL database.
    
    Parameters:
    - dbname (str): The name of the database to connect to.
    - user (str): The username for the database.
    - password (str): The password for the database.
    - host (str): The host address of the database server (default: localhost).
    - port (str): The port number of the database server (default: 5432).
    
    Returns:
    - connection: A connection object to the PostgreSQL database.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print("Successfully connected to the PostgreSQL database.")
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        return None

def insert_row(connection, table_name, row_data):
    """
    Insert a row of data into a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to insert data into.
    - row_data (dict): A dictionary where keys are column names and values are the data to insert.
    
    Returns:
    - bool: True if the insertion was successful, False otherwise.
    """
    try:
        cursor = connection.cursor()
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['%s'] * len(row_data))
        values = tuple(row_data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
        cursor.execute(query, values)
        connection.commit()
        print(f"Successfully inserted row into table {table_name}.")
        return True
    except Error as e:
        print(f"Error inserting row into table {table_name}: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def handle_client_data(client_socket, client_address, db_connection, table_name):
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
        buffer_size = 4096
        full_data = b""
        while True:
            chunk = client_socket.recv(buffer_size)
            if not chunk:
                print(f"Client {client_address} disconnected.")
                return False
            full_data += chunk
            try:
                # Try to decode and parse JSON to check if complete
                decoded_data = full_data.decode('utf-8')
                json.loads(decoded_data)
                # If JSON parsing succeeds, process the data
                print(f"Received complete data from {client_address}: {decoded_data[:100]}... (total {len(decoded_data)} characters)")
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
        print(f"Error receiving data from {client_address}: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Connect to the PostgreSQL database on Host B (replace with actual credentials)
    db_conn = connect_to_postgres(
        dbname="your_database_name",
        user="your_username",
        password="your_password",
        host="localhost",  # Adjust if database is on a different host
        port="5432"
    )
    
    if db_conn:
        server = start_tcp_server()
        if server:
            try:
                while True:
                    # Wait for a connection
                    client_socket, client_address = server.accept()
                    print(f"Connection established with {client_address}")
                    # Handle client data
                    while handle_client_data(client_socket, client_address, db_conn, "your_table_name"):
                        pass  # Continue receiving data until connection closes or error occurs
                    client_socket.close()
            except KeyboardInterrupt:
                print("\nShutting down TCP server...")
                server.close()
                db_conn.close()
                print("Database connection closed.")
            except Exception as e:
                print(f"Server error: {e}")
                server.close()
                db_conn.close()
                print("Database connection closed.")
    else:
        print("Failed to connect to the database on Host B.")
