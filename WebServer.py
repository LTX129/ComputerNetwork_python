#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys


def handleRequest(tcpSocket):
    # 1. Receive request message from the client on connection socket
    request = tcpSocket.recv(1024).decode()

    # 2. Extract the path of the requested object from the message (second part of the HTTP header)
    path = request.split()[1]

    # 3. Read the corresponding file from disk
    try:
        with open(path[1:], 'rb') as file:
            content = file.read()
    except FileNotFoundError:
        # 5. Send the correct HTTP response error
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        tcpSocket.sendall(response.encode())
        tcpSocket.close()
        return

    # 4. Store in temporary buffer
    # 6. Send the content of the file to the socket
    response = "HTTP/1.1 200 OK\r\n\r\n"
    tcpSocket.sendall(response.encode())
    tcpSocket.sendall(content)

    # 7. Close the connection socket
    tcpSocket.close()


def startServer(serverAddress, serverPort):
    # 1. Create server socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 2. Bind the server socket to server address and server port
        serverSocket.bind((serverAddress, serverPort))

        # 3. Continuously listen for connections to server socket
        serverSocket.listen(1)
        print(f"Server listening on {serverAddress}:{serverPort}")

        while True:
            # 4. When a connection is accepted, call handleRequest function, passing new connection socket
            connectionSocket, addr = serverSocket.accept()
            print(f"Connection accepted from {addr[0]}:{addr[1]}")
            handleRequest(connectionSocket)

    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        # 5. Close server socket
        serverSocket.close()


startServer("", 1314)