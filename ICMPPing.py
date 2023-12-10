#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages


def checksum(string):
    """
       Calculate the checksum of a string.

       Args:
           string (str): The input string.

       Returns:
           int: The calculated checksum.

    """
    csum = 0
    count_to = (len(string) // 2) * 2
    count = 0

    while count < count_to:
        this_val = string[count + 1] * 256 + string[count]
        csum = csum + int(this_val)
        csum = csum & 0xffffffff
        count = count + 2

    if count_to < len(string):
        csum = csum + int(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(icmp_socket, local_id, timeout, time_sent):
    """
        Receive a single ICMP ping reply.

        Args:
            icmp_socket (socket.pyi): The ICMP socket to receive the reply.
            local_id (int): The ID of the ICMP packet to match with the reply.
            timeout (float): The maximum time to wait for a reply.
            time_sent (float): The time when the ICMP packet was sent.

        Returns:
            tuple: A tuple containing the total network delay, IP TTL, and data size.
                   If a timeout occurs, returns (-1, 0, 0).
    """
    time_left = timeout
    while True:
        started_select = time.time()
        what_ready = select.select([icmp_socket], [], [], time_left)
        how_long_in_select = (time.time() - started_select)
        if not what_ready[0]:  # Timeout
            return -1, 0, 0

        time_received = time.time()
        rec_packet, _ = icmp_socket.recvfrom(1024)

        # Fetch the ICMP header from the IP packet
        icmp_header = rec_packet[20:28]

        # Unpack the header to extract the type, code, checksum, and ID
        icmp_type, _, _, packet_id, _ = struct.unpack("bbHHh", icmp_header)

        # Check that the ID matches between the request and reply
        if packet_id == local_id and icmp_type == ICMP_ECHO_REPLY:
            # Calculate the total network delay
            delay = time_received - time_sent

            # Extract the TTL from the IP header
            ip_header = rec_packet[:20]
            ip_ttl = struct.unpack("B", ip_header[8:9])[0]

            # Extract the data size from the ICMP packet
            data_size = len(rec_packet) - 28
            time_left = time_left - how_long_in_select
            if delay > timeout:
                return -1, 0, 0
            return delay, ip_ttl, data_size


def send_one_ping(icmp_socket, destination_address, local_id, data_size):
    """
        Sends a single ICMP ping packet to the specified destination address.

        Args:
            icmp_socket (socket.pyi): The ICMP socket used for sending the packet.
            destination_address (str): The destination IP address or hostname.
            local_id (int): The local identifier for the ICMP packet.
            data_size (int): The size of the data payload in the ICMP packet.

        Returns:
            float: The time of sending the ICMP packet.

    """
    my_checksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, local_id, 1)
    data = struct.pack("d", time.time()) + b"#" * (data_size - 8)

    # Calculate the checksum on the data and the header
    my_checksum = checksum(header + data)
    if sys.platform == 'darwin':
        my_checksum = socket.htons(my_checksum) & 0xffff  # 针对MacOS
    else:
        my_checksum = socket.htons(my_checksum)  # 针对其他平台

    # Insert the checksum into the header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, local_id, 1)

    # Send the packet using the socket
    icmp_socket.sendto(header + data, (destination_address, 80))

    # Record the time of sending
    time_sent = time.time()

    return time_sent


def do_one_ping(destination_address, timeout, data_size):
    """
        Perform a single ICMP ping to the specified destination address.

        Args:
            destination_address (str): The IP address or hostname to ping.
            timeout (float): The maximum time to wait for a response, in seconds.
            data_size (int): The size of the data payload to send in the ICMP packet.

        Returns:
            tuple: A tuple containing the network delay (in milliseconds), the IP time-to-live (TTL),
                   and the actual data size received in the response.

    """
    # 1. Create ICMP socket
    icmp = socket.getprotobyname('icmp')
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    local_id = os.getpid()
    # 2. Call sendOnePing function
    time_sent = send_one_ping(icmp_socket, destination_address, local_id, data_size)
    # 3. Call receiveOnePing function
    delay, ip_ttl, data_size = receive_one_ping(icmp_socket, local_id, timeout, time_sent)
    # 4. Close ICMP socket
    icmp_socket.close()
    # 5. Return total network delay
    return delay, ip_ttl, data_size


def ping(host, timeout=1, count=4, data_size=64):
    """
        Ping a host using ICMP protocol.

        Args:
            host (str): The hostname or IP address of the target host.
            timeout (float): The timeout value in seconds for each ping request. Default is 1 second.
            count (int): The number of ping requests to send. Default is 4.
            data_size (int): The size of the data payload in each ping request. Default is 64 bytes.

        Returns:
            None

        Prints out the ping statistics including the delay, TTL, and data size for each ping request.
    """
    dest_addr = socket.gethostbyname(host)
    print("Ping " + host + " (" + dest_addr + ") using Python:")
    sent = 0
    received = 0
    min_delay = float("inf")
    max_delay = 0
    total_delay = 0
    for i in range(count):
        delay, ip_ttl, data_size = do_one_ping(dest_addr, timeout, data_size)
        # Print out the returned delay, TTL, and data size
        if delay == -1:
            print("Request timed out.")
        else:
            print(
                "%d bytes from %s: icmp_seq=%d ttl=%d time=%.3f ms" % (
                    data_size, dest_addr, i + 1, ip_ttl, delay * 1000))
            sent += 1
            received += 1
            min_delay = min(min_delay, delay)
            max_delay = max(max_delay, delay)
            total_delay += delay
        time.sleep(1)
    lost = sent - received
    if sent == 0:
        loss_percent = 0
    else:
        loss_percent = lost / sent * 100
    if received == 0:
        avg_delay = 0
    else:
        avg_delay = total_delay / received
    print("\nPing statistics for %s:" % dest_addr)
    print("    Packets: Sent = %d, Received = %d, Lost = %d (%.0f%% loss)" % (sent, received, lost, loss_percent))
    if received > 0:
        print("Approximate round trip times in milli-seconds:")
        print("    Minimum = %.3fms, Maximum = %.3fms, Average = %.3fms" % (
            min_delay * 1000, max_delay * 1000, avg_delay * 1000))


ping("baidu.com")
