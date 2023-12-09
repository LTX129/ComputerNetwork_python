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
    csum = 0
    count_to = (len(string) // 2) * 2
    count = 0

    while count < count_to:
        this_val = string[count + 1] * 256 + string[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count = count + 2

    if count_to < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(icmp_socket, local_id, timeout, time_sent):
    # 1. Wait for the socket to receive a reply
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    # 3. Compare the time of receipt to time of sending, producing the total network delay
    # 4. Unpack the packet header for useful information, including the ID
    # 5. Check that the ID matches between the request and reply
    # 6. Return total network delay

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
        if packet_id == local_id and icmp_type == 0:
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
    # 1. Build ICMP header
    # 2. Checksum ICMP packet using given function
    # 3. Insert checksum into packet
    # 4. Send packet using socket
    # 5. Record time of sending

    # Build the ICMP header
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
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay, TTL, and data size
    # 4. Continue this process until stopped

    # Look up the hostname and resolve it to an IP address
    dest_addr = socket.gethostbyname(host)

    # Print out the destination address
    print("Ping " + host + " (" + dest_addr + ") using Python:")

    # Ping for the specified number of times
    sent = 0
    received = 0
    min_delay = float("inf")
    max_delay = 0
    total_delay = 0
    for i in range(count):
        # Call the doOnePing function
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

        # Wait for one second before sending the next ping
        time.sleep(1)

    # Print out the summary
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


ping("lancaster.ac.uk")
