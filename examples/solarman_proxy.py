""" Modbus RTU over TCP to Solarman proxy

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

import asyncio
from pysolarmanv5 import PySolarmanV5Async, V5FrameError, NoSocketAvailableError


async def handle_client(reader, writer):
    solarmanv5 = PySolarmanV5Async(
        "192.168.1.24", 123456789, verbose=True, auto_reconnect=True
    )
    await solarmanv5.connect()

    addr = writer.get_extra_info("peername")

    print(f"{addr}: New connection")

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
    print(f"{addr}: Connection closed")
    await solarmanv5.disconnect()


async def run_server():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 1502)
    async with server:
        await server.serve_forever()


asyncio.run(run_server())
