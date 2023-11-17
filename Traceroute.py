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

    answer = socket.htons(answer)

    return answer

def create_packet(id):
    """
    Create a new echo request packet based on the given "id".
    """
    header = struct.pack('bbHHh', 8, 0, 0, id, 1)
    data = 192 * 'Q'
    my_checksum = checksum(header + data.encode('utf-8'))
    header = struct.pack('bbHHh', 8, 0, my_checksum, id, 1)
    return header + data.encode('utf-8')

def traceroute(host, max_hops=30, timeout=2):
    """trace
    Run the traceroute to the given destination address (dest_addr).
    """
    dest_addr = socket.gethostbyname(host)
    icmp_proto = socket.getprotobyname('icmp')
    ttl = 1
    print(f"通过最多 {max_hops} 个跃点跟踪")
    # print(f"到 {dest_addr} 的路由:\n")
    print("到 " + host + " (" + dest_addr + ") 的路由 using Python:")


    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto)

        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
        # Timeout for the socket to wait for a reply
        recv_socket.settimeout(timeout)
        recv_socket.bind(("", 0))

        id = os.getpid() & 0xFFFF

        packet = create_packet(id)
        send_socket.sendto(packet, (dest_addr, 1))

        try:
            started_select = time.time()
            what_ready = select.select([recv_socket], [], [], timeout)
            how_long_in_select = (time.time() - started_select)
            if what_ready[0] == []:  # Timeout
                print(f"{ttl:4}   *        *        *     请求超时。")
            recv_packet, addr = recv_socket.recvfrom(1024)
            time_received = time.time()
            time_passed = round((time_received - started_select) * 1000)
            print(f"{ttl:4}  {time_passed} ms    {time_passed} ms    {time_passed} ms  {addr[0]}")
        except socket.timeout:  # No reply within timeout
            print(f"{ttl:4}   *        *        *     请求超时。")
        finally:
            send_socket.close()
            recv_socket.close()

        ttl += 1
        if addr[0] == socket.gethostbyname(dest_addr) or ttl > max_hops:
            break

    print("\n跟踪完成。")

# Example usage
traceroute("lancaster.ac.uk")
