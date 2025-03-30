import asyncio
import ipaddress
import socket
import subprocess
import sys
import platform
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

MagicONE = "WIFIKIT-214028-READ"
MagicTWO = "HF-A11ASSISTHREAD"
ProbeExecutor = ThreadPoolExecutor(max_workers=100)


class SolarmanProbe:

    def __init__(self, address: str):
        self.addr = address
        self.found = False
        self.MAC = None
        self.SERIAL = None

    async def run(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(ProbeExecutor, self.scan)

    def scan(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.addr, 48899))
        sock.settimeout(0.5)
        sock.sendall(MagicONE.encode())
        data = None
        try:
            data = sock.recv(1024)
        except socket.timeout:
            try:
                sock.settimeout(0.5)
                sock.sendall(MagicTWO.encode())
                data = sock.recv(1024)
            except:
                pass
        except:
            pass
        if data is not None:
            data = data.decode().strip().split(",")
            self.MAC = data[1]
            self.SERIAL = data[2]
            self.found = True

    def __format__(self, format_spec):
        return (
            f"<SolarmanLogger> addr: {self.addr} mac: {self.MAC} serial: {self.SERIAL}"
        )


def get_address(iface: str) -> Optional[str]:
    proc = subprocess.Popen(
        ["ip", "addr", "show", iface], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    proc.wait()
    stdout = proc.stdout
    if proc.returncode != 0:
        return
    stdout = stdout.read().decode().split("\n")
    addr = None
    for l in stdout:
        if "inet" in l and "inet6" not in l:
            addr = l.strip(" ").split(" ")[1]
    if addr is None or addr == "":
        return None
    return addr


def gen_ips(address: str) -> List[str]:
    addr = []
    try:
        iface = ipaddress.ip_interface(address)
        if iface.ip.is_link_local or iface.ip.is_loopback or iface.ip.is_multicast:
            return addr
        addr = [str(h) for h in iface.network.hosts() if h != iface.ip]
    except Exception as e:
        print(f"{e}")
        return addr
    return addr


async def aio_main(probes: List[SolarmanProbe]):
    loop = asyncio.get_running_loop()
    coro = [r.run() for r in probes]
    print(f"Starting scan with {len(coro)} probes")
    await asyncio.gather(*coro)
    for p in probes:
        if p.found:
            print(f"{p}")


def main():
    if platform.system().lower() != "linux":
        print(f"This platform is not supported")
        sys.exit(1)
    args = sys.argv[1:]
    if len(args) == 0:
        print(f"{sys.argv[0]} requires an interface name (e.g. eth0)")
        sys.exit(1)
    local_addr = get_address(args[0])
    if local_addr is None:
        print(f"{args[0]} seems to be an invalid interface name")
        sys.exit(1)
    ips = gen_ips(local_addr)
    loop = asyncio.new_event_loop()
    probes = [SolarmanProbe(ip) for ip in ips]
    loop.run_until_complete(aio_main(probes))


if __name__ == "__main__":
    main()
