"""Modbus RTU over TCP to Solarman proxy

Can be used with Home Assistant's native Modbus integration using config below:

- name: "solarman-modbus-proxy"
  type: rtuovertcp
  host: 192.168.1.20
  port: 1502
  delay: 3
  retry_on_empty: true
  sensors:
    [...]

"""

import argparse
import asyncio
import sys
from functools import partial

from pysolarmanv5 import PySolarmanV5Async


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    logger_address: str,
    logger_serial: int,
):
    solarmanv5 = PySolarmanV5Async(
        logger_address, logger_serial, verbose=True, auto_reconnect=True
    )
    await solarmanv5.connect()

    addr = writer.get_extra_info("peername")

    print(f"{addr}: New connection")

    try:
        while True:
            modbus_request = await reader.read(1024)
            if not modbus_request:
                break
            try:
                reply = await solarmanv5.send_raw_modbus_frame(modbus_request)
                writer.write(reply)
            except:
                pass

        await writer.drain()
    except OSError:
        # https://github.com/python/cpython/issues/83037
        pass

    print(f"{addr}: Connection closed")
    await solarmanv5.disconnect()


async def run_proxy(
    bind_address: str, port: int, logger_address: str, logger_serial: int
):
    server = await asyncio.start_server(
        partial(
            handle_client, logger_address=logger_address, logger_serial=logger_serial
        ),
        bind_address,
        port,
    )
    async with server:
        print(f"Listening on {bind_address}:{port}")
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(
        prog="solarman rtu proxy",
        description="A Modbus RTU over TCP Proxy for Solarman loggers",
    )
    parser.add_argument(
        "-b", "--bind", default="0.0.0.0", help="The address to listen on"
    )
    parser.add_argument(
        "-p", "--port", default=1502, type=int, help="The TCP port to listen on"
    )
    parser.add_argument(
        "-l", "--logger", required=True, help="The IP address of the logger"
    )
    parser.add_argument(
        "-s",
        "--serial",
        required=True,
        type=int,
        help="The serial number of the logger",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_proxy(args.bind, args.port, args.logger, args.serial))
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
