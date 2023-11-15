#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)

    return answer


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header
    # 2. Checksum ICMP packet using given function
    # 3. Insert checksum into packet
    # 4. Send packet using socket
    # 5. Record time of sending

    # Build the ICMP header
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the header
    myChecksum = checksum(header + data)

    # Insert the checksum into the header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(myChecksum), ID, 1)

    # Send the packet using the socket
    icmpSocket.sendto(header + data, (destinationAddress, 1))

    # Record the time of sending
    timeSent = time.time()

    return timeSent


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, timeSent):
    # 1. Wait for the socket to receive a reply
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    # 3. Compare the time of receipt to time of sending, producing the total network delay
    # 4. Unpack the packet header for useful information, including the ID
    # 5. Check that the ID matches between the request and reply
    # 6. Return total network delay

    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([icmpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return -1

        timeReceived = time.time()
        recPacket, addr = icmpSocket.recvfrom(1024)

        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]

        # Unpack the header to extract the type, code, checksum, and ID
        icmpType, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        # Check that the ID matches between the request and reply
        if packetID == ID:
            # Calculate the total network delay
            delay = timeReceived - timeSent
            return delay

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return -1


def doOnePing(destinationAddress, timeout):
    # 1. Create ICMP socket
    # 2. Call sendOnePing function
    # 3. Call receiveOnePing function
    # 4. Close ICMP socket
    # 5. Return total network delay

    # Create the ICMP socket
    icmp = socket.getprotobyname("icmp")
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    # Generate a unique ID for the ICMP packet
    ID = os.getpid() & 0xFFFF

    # Call the sendOnePing function
    timeSent = sendOnePing(icmpSocket, destinationAddress, ID)

    # Call the receiveOnePing function
    delay = receiveOnePing(icmpSocket, destinationAddress, ID, timeout, timeSent)

    # Close the ICMP socket
    icmpSocket.close()

    # Return the total network delay
    return delay


def ping(host, timeout=1):
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped

    # Look up the hostname and resolve it to an IP address
    destAddr = socket.gethostbyname(host)

    # Print out the destination address
    print("Ping " + host + " (" + destAddr + ") using Python:")

    # Ping approximately every second
    while True:
        delay = doOnePing(destAddr, timeout)
        if delay == -1:
            print("Request timed out.")
        else:
            print("Reply from " + destAddr + ": time=%.2fms" % (delay * 1000))

        time.sleep(1)


ping("lancaster.ac.uk")