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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 1. 等待套接字接收回复
    start_time = time.time()
    what_ready = select.select([icmpSocket], [], [], timeout)
    # 2. 如果接收到回复，则记录接收时间；否则，处理超时
    if what_ready[0] == []:
        return None
    time_received = time.time()
    # 3. 比较接收时间和发送时间，计算总网络延迟
    total_time = time_received - start_time
    # 4. 解包数据包头以获取有用信息，包括ID
    packet_data = icmpSocket.recv(1024)
    icmp_header = packet_data[20:28]
    icmp_type, icmp_code, icmp_checksum, icmp_packet_id, icmp_sequence = struct.unpack("bbHHh", icmp_header)
    # 5. 检查请求和回复之间的ID是否匹配
    if icmp_packet_id != ID:
        return None
    # 6. 返回总网络延迟
    return total_time * 1000


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header
    # 2. Checksum ICMP packet using given function
    # 3. Insert checksum into packet
    # 4. Send packet using socket
    #  5. Record time of sending
    pass  # Remove/replace when function is complete


def doOnePing(destinationAddress, timeout):
    # 1. Create ICMP socket
    # 2. Call sendOnePing function
    # 3. Call receiveOnePing function
    # 4. Close ICMP socket
    # 5. Return total network delay
    pass  # Remove/replace when function is complete


def ping(host, timeout=1):
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    pass  # Remove/replace when function is complete


ping("lancaster.ac.uk")

