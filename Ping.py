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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout, timeSent, dataSize):
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
            return -1, 0, 0

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

            # Extract the TTL from the IP header
            ipHeader = recPacket[:20]
            ipTTL = struct.unpack("B", ipHeader[8:9])[0]

            # Extract the data size from the ICMP packet
            dataSize = len(recPacket) - 28

            return delay, ipTTL, dataSize

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return -1, 0, 0


def sendOnePing(icmpSocket, destinationAddress, ID, dataSize):
    # 1. Build ICMP header
    # 2. Checksum ICMP packet using given function
    # 3. Insert checksum into packet
    # 4. Send packet using socket
    # 5. Record time of sending

    # Build the ICMP header
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time()) + b"#" * (dataSize - 8)

    # Calculate the checksum on the data and the header
    myChecksum = checksum(header + data)

    # Insert the checksum into the header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)

    # Send the packet using the socket
    icmpSocket.sendto(header + data, (destinationAddress, 80))

    # Record the time of sending
    timeSent = time.time()

    return timeSent


def doOnePing(destinationAddress, timeout, dataSize):
    # 1. Create ICMP socket
    icmp = socket.getprotobyname('icmp')
    icmp_Socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    ID = os.getpid();
    # 2. Call sendOnePing function
    timeSent = sendOnePing(icmp_Socket, destinationAddress, ID, dataSize)
    # 3. Call receiveOnePing function
    delay, ipTTL, dataSize = receiveOnePing(icmp_Socket, destinationAddress, ID, timeout, timeSent, dataSize)
    # 4. Close ICMP socket
    icmp_Socket.close()
    # 5. Return total network delay
    return delay, ipTTL, dataSize


def ping(host, timeout=1,count= 4, dataSize=64):
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay, TTL, and data size
    # 4. Continue this process until stopped

    # Look up the hostname and resolve it to an IP address
    destAddr = socket.gethostbyname(host)

    # Print out the destination address
    print("Ping " + host + " (" + destAddr + ") using Python:")

    # Ping for the specified number of times
    sent = 0
    received = 0
    minDelay = float("inf")
    maxDelay = 0
    totalDelay = 0
    for i in range(count):
        # Call the doOnePing function
        delay, ipTTL, dataSize = doOnePing(destAddr, timeout, dataSize)

        # Print out the returned delay, TTL, and data size
        if delay == -1:
            print("Request timed out.")
        else:
            print(
                "%d bytes from %s: icmp_seq=%d ttl=%d time=%.3f ms" % (dataSize, destAddr, i + 1, ipTTL, delay * 1000))
            sent += 1
            received += 1
            minDelay = min(minDelay, delay)
            maxDelay = max(maxDelay, delay)
            totalDelay += delay

        # Wait for one second before sending the next ping
        time.sleep(1)

    # Print out the summary
    lost = sent - received
    if sent == 0:
        lossPercent = 0
    else:
        lossPercent = lost / sent * 100
    if received == 0:
        avgDelay = 0
    else:
        avgDelay = totalDelay / received
    print("\nPing statistics for %s:" % destAddr)
    print("    Packets: Sent = %d, Received = %d, Lost = %d (%.0f%% loss)" % (sent, received, lost, lossPercent))
    if received > 0:
        print("Approximate round trip times in milli-seconds:")
        print("    Minimum = %.3fms, Maximum = %.3fms, Average = %.3fms" % (
        minDelay * 1000, maxDelay * 1000, avgDelay * 1000))


ping("lancaster.ac.uk")