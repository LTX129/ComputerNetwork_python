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
    """
        Create a server socket and bind it to the specified address and port.

        Args:
            addr (str): The IP address or hostname to bind the socket to.
            port (int): The port number to bind the socket to.

        Returns:
            socket.pyi: The created server socket.

        """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((addr, port))
    server_socket.listen(5)
    print(f"Web server running on port {port}")
    return server_socket


def handle_request(client_socket, addr):
    """
        Handles the incoming client request.

        Args:
            client_socket (socket.pyi): The client socket object.
            addr (tuple): The address of the client.

        Returns:
            None
        """
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
        elif request_type == 'HEAD':
            handle_head_request(client_socket, filename)
        elif request_type == 'POST':
            handle_post_request(client_socket, filename, request)
        elif request_type == 'PUT':
            handle_put_request(client_socket, filename, request)
        elif request_type == 'DELETE':
            handle_delete_request(client_socket, filename)
        else:
            send_error_response(client_socket, error_501)

    finally:
        print("client close")
        client_socket.close()


def handle_head_request(client_socket, filename):
    """
        Handles a HEAD request from the client.

        Args:
            client_socket (socket.pyi): The client socket object.
            filename (str): The name of the file to be handled.

        Returns:
            None
        """
    if filename:
        try:
            with open(filename, 'rb') as file:
                file_content = file.read()
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type is None:
                    mime_type = 'application/octet-stream'

                response_header = "HTTP/1.1 200 OK\r\n"
                response_header += f'Content-Type: {mime_type}\r\n'
                response_header += f'Content-Length: {len(file_content)}\r\n\r\n'

                response = response_header.encode()
        except FileNotFoundError:
            response = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode()
        except Exception:
            response = 'HTTP/1.1 500 Internal Server Error\r\n\r\n'.encode()
    else:
        response = 'HTTP/1.1 400 Bad Request\r\n\r\n'.encode()

    client_socket.sendall(response)


def handle_post_request(client_socket, filename, request):
    """
        Handles a POST request by appending the content to a file and sending a response.

        Args:
            client_socket (socket.pyi): The client socket.
            filename (str): The name of the file to append the content to.
            request (str): The HTTP request.

        Raises:
            Exception: If an error occurs while handling the request.

        Returns:
            None
        """
    try:
        content = request.split('\r\n\r\n', 1)[1]
        with open(filename, 'ab') as file:
            file.write(content.encode())
        response_header = 'HTTP/1.1 201 Created\r\n\r\n'
        client_socket.sendall(response_header.encode())
    except Exception:
        send_error_response(client_socket, error_500)


def handle_get_request(client_socket, filename):
    """
        Handles a GET request from a client.

        Args:
            client_socket (socket.pyi): The client socket object.
            filename (str): The name of the file to be retrieved.

        Returns:
            None
        """
    if filename:
        try:
            with open(filename, 'rb') as file:
                file_content = file.read()
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
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
    """
        Handles a PUT request by saving the content to a file.

        Args:
            client_socket (socket.pyi): The client socket.
            filename (str): The name of the file to save the content to.
            request (str): The HTTP request.

        Raises:
            Exception: If an error occurs while handling the request.

        Returns:
            None
        """
    try:
        content = request.split('\r\n\r\n', 1)[1]
        with open(filename, 'wb') as file:
            file.write(content.encode())
        response_header = 'HTTP/1.1 201 Created\r\n\r\n'
        client_socket.sendall(response_header.encode())
    except Exception:
        send_error_response(client_socket, error_500)


def handle_delete_request(client_socket, filename):
    """
        Handles a DELETE request by deleting the specified file.

        Args:
            client_socket (socket.pyi): The client socket object.
            filename (str): The name of the file to be deleted.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            Exception: If an error occurs while deleting the file.

        Returns:
            None
        """
    try:
        os.remove(filename)
        response_header = 'HTTP/1.1 200 OK\r\n\r\n'
        client_socket.sendall(response_header.encode())
    except FileNotFoundError:
        send_error_response(client_socket, error_404)
    except Exception:
        send_error_response(client_socket, error_500)


def send_error_response(client_socket, error_message):
    """
        Function to send an error response to the client.

        Parameters:
        client_socket (socket.pyi): The client socket to send the response to.
        error_message (str): The error message to include in the response.

        Returns:
        None
    """
    response_header = f'HTTP/1.1 {error_message}\r\n\r\n'
    client_socket.sendall(response_header.encode())


def extract_request_type_and_filename(request_line):
    """
        Extracts the request type and filename from the HTTP request.

        Args:
            request_line (str): The HTTP request line.

        Returns:
            tuple: A tuple containing the request type and filename.
                   The request type is a string and the filename is a string without leading or trailing slashes.

    """
    parts = request_line.split()
    if len(parts) > 1:
        return parts[0], parts[1].strip('/')
    return None, None


def start_server(server_addr, port):
    """
        Starts the multi-thread web server on the specified address and port.

        Args:
            server_addr (str): The server address.
            port (int): The port number.

        Returns:
            None
    """
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
