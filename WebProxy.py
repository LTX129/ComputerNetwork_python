
import socket
import os

# Define a simple cache structure
cache = {}

def create_server_socket(addr, port):
    # Create a socket and bind to the specified port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((addr, port))
    server_socket.listen(5)
    print(f"Web Proxy running on port {port}")
    return server_socket

def handle_request(client_socket):
    # Handle the incoming client request
    request = client_socket.recv(2048).decode()
    print(f"Request received: {request.splitlines()[0]}")

    # Extract the URL from the GET request
    url = extract_url(request)
    if url in cache:
        print("Cache hit. Returning cached response.")
        response = cache[url]
    else:
        print("Cache miss. Forwarding request to server.")
        response = forward_request(url)
        cache[url] = response

    client_socket.sendall(response)
    client_socket.close()

def extract_url(request):
    # Extract the URL from the request
    lines = request.splitlines()
    if lines:
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) > 1 and parts[0] == 'GET':
            return parts[1].strip('/')

def forward_request(url):
    # Forward the request to the actual web server and return the response
    server_socket = socket.create_connection(('', 2000))
    server_socket.sendall(f'GET /{url} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n'.encode())
    response = server_socket.recv(4096)
    server_socket.close()
    return response

def proxy(port):
    try:
        server_socket = create_server_socket('', port)
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection accepted from {addr}")
            handle_request(client_socket)
    except KeyboardInterrupt:
        print("Shutting down the proxy.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    port = input("Please enter the port of the proxy: ")
    proxy(port)
