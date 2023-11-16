import socket
import os
import time
import select

def receiveOnePing(udpSocket, timeout, timeSent):
    # Wait for the socket to receive a reply
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([udpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if not whatReady[0]:  # Timeout
            return -1

        timeReceived = time.time()
        recPacket, addr = udpSocket.recvfrom(1024)
        delay = timeReceived - timeSent
        return delay

def sendOnePing(udpSocket, destinationAddress, port):
    # Send packet using socket
    udpSocket.sendto(b'', (destinationAddress, port))
    # Record time of sending
    timeSent = time.time()
    return timeSent

def doOnePing(destinationAddress, port, timeout):
    # Create the UDP socket
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Call the sendOnePing function
    timeSent = sendOnePing(udpSocket, destinationAddress, port)

    # Call the receiveOnePing function
    delay = receiveOnePing(udpSocket, timeout, timeSent)

    # Close the UDP socket
    udpSocket.close()

    return delay

def ping(host, port=33434, timeout=1, count=4):
    # Look up hostname, resolving it to an IP address
    destAddr = socket.gethostbyname(host)
    print("Pinging " + host + " (" + destAddr + ") using UDP:")

    # Ping for the specified number of times
    for i in range(count):
        delay = doOnePing(destAddr, port, timeout)
        if delay == -1:
            print("Request timed out.")
        else:
            print("Reply from %s: time=%.3fms" % (destAddr, delay * 1000))
        time.sleep(1)

ping("lancaster.ac.uk")
