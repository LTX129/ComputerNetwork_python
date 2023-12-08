
import socket
import os
import threading

def create_server_socket(addr,port):
    # Create a socket and bind to the specified port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((addr, port))
    server_socket.listen(5)
    print(f"Web server running on port {port}")
    return server_socket

def handle_request(client_socket, addr):
    # Handle the incoming client request
    try:
        request = client_socket.recv(4096).decode()
        request_lines = request.splitlines()
        if request_lines:
            print(f"request line: {request_lines[0]}")
        else:
            print("Received empty request")
            return

        filename = extract_file_name(request_lines[0])

        if filename:
            try:
                with open(filename, 'rb') as file:
                    file_content = file.read()
                    response_header = 'HTTP/1.1 200 OK\r\n'
                    response_header += 'Content-Type: text/html; charset=utf-8\r\n'
                    response_header += f'Content-Length: {len(file_content)}\r\n\r\n'
                    response = response_header.encode() + file_content
            except FileNotFoundError:
                response_header = 'HTTP/1.1 404 Not Found\r\n\r\n'
                response_body = 'File not found'
                response = response_header.encode() + response_body.encode()
        else:
            response_header = 'HTTP/1.1 400 Bad Request\r\n\r\n'
            response_body = 'Bad Request'
            response = response_header.encode() + response_body.encode()

        client_socket.sendall(response)
    finally:
        print("client close")
        client_socket.close()

def extract_file_name(request_line):
    # Extract the file name from the HTTP GET request
    parts = request_line.split()
    if len(parts) > 1 and parts[0] == 'GET':
        return parts[1].strip('/')

def startServer(serveraddr, port):
    try:
        server_socket = create_server_socket(serveraddr, port)
        while True:
            client_socket, addr = server_socket.accept()
            print(f"one connection is established and it's address is: {addr}")
            print(f"Connection accepted from {addr[0]}:{addr[1]}")
            client_thread = threading.Thread(target=handle_request, args=(client_socket, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down the server.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    port = input("Please enter the port of the proxy: ")
    startServer("", port)
