""" Scan local network for Solarman data loggers """

import socket


def main():
    """Solarman data logger scanner"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1.0)

    request = "WIFIKIT-214028-READ"
    address = ("<broadcast>", 48899)

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


if __name__ == "__main__":
    main()
