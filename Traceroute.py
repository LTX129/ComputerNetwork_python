import socket
import os
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
# 使用您提供的 checksum 函数
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

def traceroute(dest_name, max_hops=30, timeout=1):
    dest_addr = socket.gethostbyname(dest_name)
    print(f'Traceroute to {dest_name} ({dest_addr})')

    icmp = socket.getprotobyname('icmp')
    for ttl in range(1, max_hops + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp) as send_sock:
            # 设置 TTL
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I',ttl))

            # 创建 ICMP echo 请求的头部和数据
            my_checksum = 0
            packet_id = os.getpid() & 0xFFFF
            header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, my_checksum, packet_id, 1)
            data = struct.pack('!d', time.time())
            my_checksum = checksum(header + data)
            header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, my_checksum, packet_id, 1)
            packet = header + data

            send_sock.sendto(packet, (dest_addr, 1))

            start_time = time.time()
            while True:
                ready = select.select([send_sock], [], [], timeout)
                if ready[0] == []:
                    print(f'{ttl}\t*')
                    break

                time_received = time.time()
                rec_packet, addr = send_sock.recvfrom(1024)

                icmp_header = rec_packet[20:28]
                icmp_type, _, _, _, _ = struct.unpack('!BBHHH', icmp_header)

                if icmp_type == 11:  # Time Exceeded
                    print(f'{ttl}\t{addr[0]}\t{(time_received - start_time) * 1000:.2f} ms')
                    break
                elif icmp_type == 0:  # Echo Reply
                    print(f'{ttl}\t{addr[0]}\t{(time_received - start_time) * 1000:.2f} ms')
                    return

traceroute("www.baidu.com")