"""Scan local network for Solarman data loggers"""

import socket
from argparse import ArgumentParser


def scan(broadcast_address: str):
    """Solarman data logger scanner"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1.0)

    request = "WIFIKIT-214028-READ"
    address = (broadcast_address, 48899)

    sock.sendto(request.encode(), address)
    while True:
        try:
            data = sock.recv(1024)
        except socket.timeout:
            break
        keys = dict.fromkeys(["ipaddress", "mac", "serial"])
        values = data.decode().split(",")
        result = dict(zip(keys, values))
        print(result)


def main():
    parser = ArgumentParser(
        "solarman-scan", description="Scanner for IGEN/Solarman dataloggers"
    )
    parser.add_argument("broadcast", help="Network broadcast address")
    opts = parser.parse_args()
    scan(opts.broadcast)


if __name__ == "__main__":
    main()
