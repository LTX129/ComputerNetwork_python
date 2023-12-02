import socket
import os

def create_server_socket(addr,port):
    # Create a socket and bind to the specified port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((addr, port))
    server_socket.listen(1)
    print(f"Web server running on port {port}")
    return server_socket

def handle_request(client_socket, addr):
    # Handle the incoming client request
    request = client_socket.recv(1024).decode()
    print(f"request line: {request.splitlines()[0]}")
    filename = extract_file_name(request)

    if filename:
        try:
            with open(filename, 'rb') as file:
                response = 'HTTP/1.1 200 OK\n\n'.encode() + file.read()
        except FileNotFoundError:
            response = 'HTTP/1.1 404 Not Found\n\nFile not found'.encode()
    else:
        response = 'HTTP/1.1 400 Bad Request\n\n'.encode()

    client_socket.sendall(response)
    print("client close")
    client_socket.close()

def extract_file_name(request):
    # Extract the file name from the HTTP GET request
    lines = request.splitlines()
    if lines:
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) > 1 and parts[0] == 'GET':
            return parts[1].strip('/')

def startServer(serveraddr, port):
    try:
        server_socket = create_server_socket(serveraddr, port)
        while True:
            client_socket, addr = server_socket.accept()
            print(f"one connection is established and it's address is: {addr}")
            print(f"Connection accepted from {addr[0]}:{addr[1]}")
            handle_request(client_socket, addr)
    except KeyboardInterrupt:
        print("Shutting down the server.")
    finally:
        server_socket.close()

startServer("", 1314)