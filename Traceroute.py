import os
import sys
import socket
import struct
import select
import time

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages


# Provided checksum function from the coursework material
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

    return answer


def create_packet(id):
    """
    Create a new echo request packet based on the given "id".
    """
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, id, 1)
    data = 192 * 'Q'
    my_checksum = checksum(header + data.encode('utf-8'))
    # 针对不同操作系统进行校验和的字节顺序转换
    if sys.platform == 'darwin':
        # MacOS系统需要转换校验和的字节顺序并保证其为16位
        my_checksum = socket.htons(my_checksum) & 0xffff
    else:
        # 其他系统转换校验和的字节顺序
        my_checksum = socket.htons(my_checksum)

    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, my_checksum, id, 1)

    return header + data.encode('utf-8')


def sendOnePing(send_socket, dest_addr, ID):
    """
    Send one ping to the destination address using the given socket.
    """
    packet = create_packet(ID)
    send_socket.sendto(packet, (dest_addr, 1))


def doOnePing(dest_addr, ttl, timeout):
    """
    Perform three ping operations and return the time measurements.
    """
    icmp_proto = socket.getprotobyname('icmp')
    delays = []
    for _ in range(3):  # Three measurements
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto) as send_socket, \
                socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto) as recv_socket:
            send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
            recv_socket.bind(("", 0))

            ID = os.getpid() & 0xFFFF
            sendOnePing(send_socket, dest_addr, ID)
            recv_socket.settimeout(timeout)

            try:
                started_select = time.time()
                what_ready = select.select([recv_socket], [], [], timeout)
                if what_ready[0] == []:  # Timeout
                    delays.append('*')
                    continue
                recv_packet, addr = recv_socket.recvfrom(1024)
                time_received = time.time()
                bytes = struct.calcsize("d")
                t = struct.unpack("d", recv_packet[28:28 + bytes])[0]
                icmpHeader = recv_packet[20:28]
                icmpType, _, _, packetID, _ = struct.unpack("bbHHh", icmpHeader)

                if packetID == ID or (icmpType == 11 or icmpType == 3):
                    delays.append(f"{(time_received - started_select) * 1000:.0f} ms")
                elif packetID == ID or icmpType == 0:
                    delays.append(f"{(time_received - t) * 1000:.0f} ms")
                else:
                    delays.append('*')
            except socket.timeout:
                delays.append('*')

    return ttl, addr[0] if 'addr' in locals() and addr else None, delays


def traceroute(host, max_hops=30, timeout=1):
    packets_sent, packets_received, total_time = 0, 0, []

    """
    Run the traceroute to the given host.
    """
    dest_addr = socket.gethostbyname(host)
    print(f"Trace the route to {host} [{dest_addr}] by up to {max_hops} hops:\n")

    for ttl in range(1, max_hops + 1):
        ttl, addr, delays = doOnePing(dest_addr, ttl, timeout)
        delay_strs = ' '.join(delays)
        # 尝试将IP地址解析为域名
        resolved_name = addr
        if addr:
            try:
                resolved_name = socket.gethostbyaddr(addr)[0]
            except socket.herror:
                # 如果无法解析IP地址，保留原始IP地址
                pass
        print(f"{ttl:2}   {delay_strs}  {addr if addr else 'Request Timeout。'} [{resolved_name}]")

        packets_sent += 3  # 3 pings per TTL
        packets_received += len([d for d in delays if '*' not in d])
        total_time.extend([float(d[:-3]) for d in delays if '*' not in d])

        if addr == dest_addr:
          break

# Summary
    packets_lost = packets_sent - packets_received
    loss_percentage = (packets_lost / packets_sent) * 100 if packets_sent else 0
    min_time = min(total_time) if total_time else 0
    max_time = max(total_time) if total_time else 0
    avg_time = sum(total_time) / len(total_time) if total_time else 0
    print(f"\n{dest_addr}Traceroute statistics:")
    print(
        f"    Data packet: sent = {packets_sent}, Received = {packets_received}, Lost = {packets_lost} ({loss_percentage:.0f}% Lost)，")
    print(f"Estimated time of round trip in milliseconds:")
    print(f"    min = {min_time:.0f}ms，max = {max_time:.0f}ms，average = {avg_time:.0f}ms")

# Example usage
traceroute("lancaster.ac.uk")