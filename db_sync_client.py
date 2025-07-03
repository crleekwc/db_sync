import socket

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

def send_hello_world(client_socket):
    """
    Send the string 'Hello World!' over the socket connection.
    
    Parameters:
    - client_socket: The socket object for the client connection.
    
    Returns:
    - bool: True if the data was sent successfully, False otherwise.
    """
    try:
        message = "Hello World!"
        client_socket.sendall(message.encode('utf-8'))
        print(f"Sent message: {message}")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

# Example usage
if __name__ == "__main__":
    client = connect_to_tcp_server()
    if client:
        try:
            # Send "Hello World!" message
            if send_hello_world(client):
                print("Message sent successfully.")
            else:
                print("Failed to send message.")
            client.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Client error: {e}")
            client.close()
