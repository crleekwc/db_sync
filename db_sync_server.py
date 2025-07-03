import socket

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

def handle_client_data(client_socket, client_address):
    """
    Receive data from a client over the TCP socket and print it to stdout.
    
    Parameters:
    - client_socket: The socket object for the client connection.
    - client_address: The address of the connected client.
    
    Returns:
    - bool: True if data was received and processed, False if the connection was closed or an error occurred.
    """
    try:
        # Receive data from the client
        data = client_socket.recv(1024)
        if data:
            print(f"Received data from {client_address}: {data.decode('utf-8')}")
            return True
        else:
            print(f"Client {client_address} disconnected.")
            return False
    except Exception as e:
        print(f"Error receiving data from {client_address}: {e}")
        return False

# Example usage
if __name__ == "__main__":
    server = start_tcp_server()
    if server:
        try:
            while True:
                # Wait for a connection
                client_socket, client_address = server.accept()
                print(f"Connection established with {client_address}")
                # Handle client data
                while handle_client_data(client_socket, client_address):
                    pass  # Continue receiving data until connection closes or error occurs
                client_socket.close()
        except KeyboardInterrupt:
            print("\nShutting down TCP server...")
            server.close()
        except Exception as e:
            print(f"Server error: {e}")
            server.close()
