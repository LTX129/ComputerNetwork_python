import socket

# Define a simple cache structure
cache = {}


def create_server_socket(addr, local_port):
    # Create a socket and bind to the specified port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((addr, local_port))
    server_socket.listen(5)
    print(f"Web Proxy running on port {local_port}")
    return server_socket


def handle_request(client_socket):
    # Handle the incoming client request
    request = client_socket.recv(2048).decode()

    # Check if the request is not empty
    if not request:
        print("Received empty request")
        client_socket.close()
        return

    print(f"Request received: {request.splitlines()[0]}")

    # Extract the request type and URL
    request_type, url = extract_request_type_and_url(request)

    if request_type == 'GET' and url in cache:
        print("Cache hit. Returning cached response.")
        response = cache[url]
    else:
        print("Cache miss. Forwarding request to server.")
        response = forward_request(request)
        if request_type == 'GET':
            cache[url] = response

    client_socket.sendall(response)
    client_socket.close()


def extract_request_type_and_url(request):
    # Extract the request type and URL from the request
    lines = request.splitlines()
    if lines:
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) > 1:
            return parts[0], parts[1].strip('/')
    return None, None

def forward_request(full_request):
    # Forward the request to the actual web server and return the response
    server_socket = socket.create_connection(('127.0.0.1', 8000))  # Adjust as needed
    server_socket.sendall(full_request.encode())  # Forward the full request
    response = server_socket.recv(4096)
    server_socket.close()
    return response



def proxy(local_port):
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
