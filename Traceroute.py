import os
import sys
import socket
import struct
import select
import time

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_ECHO_UNREACHABLE = 3
ICMP_ECHO_TTL0 = 11


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


def create_packet(local_id):
    """
        Create a new echo request packet based on the given "id".

        Args:
            local_id (int): The local identifier for the packet.

        Returns:
            bytes: The echo request packet.

        Raises:
            None.
    """
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, local_id, 1)
    data = 192 * 'Q'
    my_checksum = checksum(header + data.encode('utf-8'))
    # 针对不同操作系统进行校验和的字节顺序转换
    if sys.platform == 'darwin':
        # MacOS系统需要转换校验和的字节顺序并保证其为16位
        my_checksum = socket.htons(my_checksum) & 0xffff
    else:
        # 其他系统转换校验和的字节顺序
        my_checksum = socket.htons(my_checksum)

    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, my_checksum, local_id, 1)

    return header + data.encode('utf-8')


def send_one_ping(send_socket, dest_addr, local_id):
    """
    Send one ping to the destination address using the given socket.

    Args:
        send_socket (socket.pyi): The socket used to send the ping.
        dest_addr (str): The destination address to send the ping to.
        local_id (int): The local ID of the ping packet.

    Returns:
        None
    """
    packet = create_packet(local_id)
    send_socket.sendto(packet, (dest_addr, 1))


def do_one_ping(dest_addr, ttl, timeout):
    """
    Perform three ping operations and return the time measurements.

    Args:
        dest_addr (str): The destination address to ping.
        ttl (int): The time-to-live value for the ping packets.
        timeout (float): The timeout value for each ping operation.

    Returns:
        tuple: A tuple containing the time-to-live value, the destination address (if available), and the time measurements.

    """
    icmp_proto = socket.getprotobyname('icmp')
    delays = []
    for _ in range(3):  # Three measurements
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto) as send_socket, \
                socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto) as recv_socket:
            send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
            recv_socket.bind(("", 0))

            local_id = os.getpid() & 0xFFFF
            send_one_ping(send_socket, dest_addr, local_id)
            recv_socket.settimeout(timeout)

            try:
                started_select = time.time()
                what_ready = select.select([recv_socket], [], [], timeout)
                if not what_ready[0]:  # Timeout
                    delays.append('*')
                    continue
                recv_packet, addr = recv_socket.recvfrom(1024)
                time_received = time.time()
                bytes_num = struct.calcsize("d")
                t = struct.unpack("d", recv_packet[28:28 + bytes_num])[0]
                icmp_header = recv_packet[20:28]
                icmp_type, _, _, packet_id, _ = struct.unpack("bbHHh", icmp_header)
                if packet_id == local_id or (icmp_type == ICMP_ECHO_TTL0 or icmp_type == ICMP_ECHO_UNREACHABLE):
                    delays.append(f"{(time_received - started_select) * 1000:.0f} ms")
                elif packet_id == local_id or icmp_type == ICMP_ECHO_REPLY:
                    delays.append(f"{(time_received - t) * 1000:.0f} ms")
                else:
                    delays.append('*')
            except socket.timeout:
                delays.append('*')

    return ttl, addr[0] if 'addr' in locals() and addr else None, delays


def traceroute(host, max_hops=30, timeout=1):
    """
        Run the traceroute to the given host.

        Args:
            host (str): The hostname or IP address of the destination.
            max_hops (int, optional): The maximum number of hops to trace. Defaults to 30.
            timeout (int, optional): The timeout value for each hop in seconds. Defaults to 1.

        Returns:
            None
    """
    packets_sent, packets_received, total_time = 0, 0, []
    # Run the traceroute to the given host.
    dest_addr = socket.gethostbyname(host)
    print(f"Trace the route to {host} [{dest_addr}] by up to {max_hops} hops:\n")

    for ttl in range(1, max_hops + 1):
        ttl, addr, delays = do_one_ping(dest_addr, ttl, timeout)
        delay_strs = ' '.join(delays)
        # Attempts to resolve an IP address to a domain name
        resolved_name = addr
        if addr:
            try:
                resolved_name = socket.gethostbyaddr(addr)[0]
            except socket.herror:
                # If the IP address cannot be resolved, retain the original IP address
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
    print("Estimated time of round trip in milliseconds:")
    print(f"    min = {min_time:.0f}ms，max = {max_time:.0f}ms，average = {avg_time:.0f}ms")


# Example usage
if __name__ == "__main__":
    host_str = str(sys.argv[1])
    traceroute(host_str)
