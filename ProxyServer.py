import socket

# Define a simple cache structure
cache = {}


def create_server_socket(addr, local_port):
    """
        Create a server socket and bind it to the specified address and port.

        Args:
            addr (str): The IP address to bind the socket to.
            local_port (int): The port number to bind the socket to.

        Returns:
            socket.pyi: The created server socket.

    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((addr, local_port))
    server_socket.listen(5)
    print(f"Web Proxy running on port {local_port}")
    return server_socket


def handle_request(client_socket):
    """
        Handles the incoming client request.

        Args:
            client_socket (socket.pyi): The client socket object.

        Returns:
            None
        """
    request = client_socket.recv(2048).decode()
    # Check if the request is not empty
    if not request:
        print("Received empty request")
        client_socket.close()
        return

    print(f"Request received: {request.splitlines()[0]}")

    # Extract the request type and URL
    request_type, url = extract_request_type_and_url(request)

    if request_type in ['GET', 'HEAD'] and url in cache and url in cache:
        print("Cache hit. Returning cached response.")
        response = cache[url]
    else:
        print("Cache miss. Forwarding request to server.")
        response = forward_request(request)
        if request_type in ['GET', 'HEAD']:
            cache[url] = response

    client_socket.sendall(response)
    client_socket.close()


def extract_request_type_and_url(request):
    """
        Extracts the request type and URL from the request.

        Args:
            request (str): The HTTP request.

        Returns:
            tuple: A tuple containing the request type and URL.

        Example:
            >>> request = "GET /index.html HTTP/1.1"
            >>> extract_request_type_and_url(request)
            ('GET', 'index.html')
    """
    lines = request.splitlines()
    if lines:
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) > 1:
            return parts[0], parts[1].strip('/')
    return None, None


def forward_request(full_request):
    """
        Forward the request to the actual web server and return the response.

        Args:
            full_request (str): The full request to be forwarded.

        Returns:
            bytes: The response received from the web server.
    """
    server_socket = socket.create_connection(('127.0.0.1', 8000))  # Adjust as needed
    server_socket.sendall(full_request.encode())  # Forward the full request
    response = server_socket.recv(4096)
    server_socket.close()
    return response


def proxy(local_port):
    """
        Starts a proxy server on the specified local port.

        Args:
            local_port (int): The local port number to listen on.

        Returns:
            None
    """
    server_socket = None
    try:
        server_socket = create_server_socket('', local_port)
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection accepted from {addr}")
            handle_request(client_socket)
    except KeyboardInterrupt:
        print("Shutting down the proxy.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    port = int(input("Please enter the port of the proxy: "))
    proxy(port)
