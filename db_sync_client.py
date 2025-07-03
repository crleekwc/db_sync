import socket
import json
import psycopg2
from psycopg2 import Error

def connect_to_tcp_server(host="localhost", port=443):
    """
    Connect to a listening TCP socket on the specified host and port.
    
    Parameters:
    - host (str): The host address of the server to connect to (default: localhost).
    - port (int): The port number of the server to connect to (default: 443).
    
    Returns:
    - client_socket: The socket object if connection is successful, None otherwise.
    """
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the server
        client_socket.connect((host, port))
        print(f"Successfully connected to TCP server at {host}:{port}")
        return client_socket
    except Exception as e:
        print(f"Error connecting to TCP server at {host}:{port}: {e}")
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

def query_table(connection, table_name):
    """
    Query all information from a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query.
    
    Returns:
    - list: A list of tuples containing the rows of data from the table.
    """
    try:
        cursor = connection.cursor()
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Successfully retrieved data from table {table_name}.")
        return rows
    except Error as e:
        print(f"Error querying table {table_name}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def send_data_over_socket(client_socket, data):
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
        print(f"Sent data over socket: {message[:100]}... (total {len(message)} characters)")
        return True
    except Exception as e:
        print(f"Error sending data over socket: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Connect to the PostgreSQL database on Host A (replace with actual credentials)
    db_conn = connect_to_postgres(
        dbname="your_database_name",
        user="your_username",
        password="your_password",
        host="host_a_ip_address",  # Replace with Host A's IP address
        port="5432"
    )
    
    if db_conn:
        # Query data from the table
        table_data = query_table(db_conn, "your_table_name")
        db_conn.close()
        print("Database connection closed.")
        
        # Connect to the TCP server on Host B
        client = connect_to_tcp_server(host="host_b_ip_address")  # Replace with Host B's IP address
        if client:
            try:
                # Send the queried data over the socket
                if send_data_over_socket(client, table_data):
                    print("Data sent successfully.")
                else:
                    print("Failed to send data.")
                client.close()
                print("Socket connection closed.")
            except Exception as e:
                print(f"Client error: {e}")
                client.close()
    else:
        print("Failed to connect to the database on Host A.")
