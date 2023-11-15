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
    # 1. 构建ICMP头
    icmp_type = 8
    icmp_code = 0
    icmp_checksum = 0
    icmp_packet_id = ID
    icmp_sequence = 1
    icmp_header = struct.pack("bbHHh", icmp_type, icmp_code, icmp_checksum, icmp_packet_id, icmp_sequence)
    # 2. 计算校验和
    icmp_checksum = checksum(icmp_header)
    # 3. 将校验和插入数据包
    icmp_header = struct.pack("bbHHh", icmp_type, icmp_code, icmp_checksum, icmp_packet_id, icmp_sequence)
    # 4. 使用套接字发送数据包
    icmp_packet = icmp_header + b"Hello, World!"
    icmpSocket.sendto(icmp_packet, (destinationAddress, 80))
    # 5. 记录发送时间
    time_sent = time.time()
    return time_sent


def doOnePing(destinationAddress, timeout):
    # 1. 创建ICMP套接字
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    # 2. 调用sendOnePing函数
    packet_id = os.getpid() & 0xFFFF
    send_time = sendOnePing(icmp_socket, destinationAddress, packet_id)
    # 3. 调用receiveOnePing函数
    total_delay = receiveOnePing(icmp_socket, packet_id, timeout, send_time)
    # 4. 关闭ICMP套接字
    icmp_socket.close()
    # 5. 返回总网络延迟
    return total_delay


def ping(host, timeout=1):
    # 1. Look up hostname, resolving it to an IP address
    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    pass  # Remove/replace when function is complete


ping("lancaster.ac.uk")

