import socket
import os
import threading
import mimetypes

N = None
error_500 = "500 Internal Server Error"
error_404 = '404 Not Found'
error_400 = '400 Bad Request'
error_501 = '501 Not Implemented'


def create_server_socket(addr, port):
    # Create a socket and bind to the specified port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        request_type, filename = extract_request_type_and_filename(request_lines[0])

        if request_type == 'GET':
            handle_get_request(client_socket, filename)
        elif request_type == 'PUT':
            handle_put_request(client_socket, filename, request)
        elif request_type == 'DELETE':
            handle_delete_request(client_socket, filename)
        else:
            send_error_response(client_socket, error_501)

    finally:
        print("client close")
        client_socket.close()


def handle_get_request(client_socket, filename):
    if filename:
        try:
            with open(filename, 'rb') as file:
                file_content = file.read()
                # 使用mimetypes库获取文件扩展名对应的MIME类型
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type is None:
                    mime_type = 'application/octet-stream'  # 默认的二进制流类型

                response_header = "HTTP/1.1 200 OK\r\n"
                response_header += f'Content-Type: {mime_type}\r\n'
                response_header += f'Content-Length: {len(file_content)}\r\n\r\n'

                response = response_header.encode() + file_content
        except FileNotFoundError:
            response_header = 'HTTP/1.1 404 Not Found\r\n\r\n'
            response_body = 'File not found'
            response = response_header.encode() + response_body.encode()
            send_error_response(client_socket, error_404)
        except Exception:
            send_error_response(client_socket, error_500)
    else:
        response_header = 'HTTP/1.1 400 Bad Request\r\n\r\n'
        response_body = 'Bad Request'
        response = response_header.encode() + response_body.encode()
        send_error_response(client_socket, error_400)

    client_socket.sendall(response)


def handle_put_request(client_socket, filename, request):
    try:
        content = request.split('\r\n\r\n', 1)[1]
        with open(filename, 'wb') as file:
            file.write(content.encode())
        response_header = 'HTTP/1.1 201 Created\r\n\r\n'
        client_socket.sendall(response_header.encode())
    except Exception:
        send_error_response(client_socket, error_500)


def handle_delete_request(client_socket, filename):
    try:
        os.remove(filename)
        response_header = 'HTTP/1.1 200 OK\r\n\r\n'
        client_socket.sendall(response_header.encode())
    except FileNotFoundError:
        send_error_response(client_socket, error_404)
    except Exception:
        send_error_response(client_socket, error_500)


def send_error_response(client_socket, error_message):
    # Function to send an error response
    response_header = f'HTTP/1.1 {error_message}\r\n\r\n'
    client_socket.sendall(response_header.encode())


def extract_request_type_and_filename(request_line):
    # Extract the file name from the HTTP request
    parts = request_line.split()
    if len(parts) > 1:
        return parts[0], parts[1].strip('/')
    return None, None


def start_server(server_addr, port):
    server_socket = None
    try:
        server_socket = create_server_socket(server_addr, port)
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
    port_input = int(input("Please enter the port of the server: "))
    start_server("", port_input)
