import struct
import socket
import threading
import socketserver
import asyncio
import random
import logging
import platform

from umodbus.client.serial.redundancy_check import add_crc
from umodbus.functions import (
    ReadHoldingRegisters,
    ReadInputRegisters,
    ReadCoils,
    create_function_from_request_pdu,
)

from pysolarmanv5.pysolarmanv5 import CONTROL_CODE, PySolarmanV5, V5FrameError


_WIN_PLATFORM = True if platform.system() == "Windows" else False
socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer.allow_reuse_port = True
log = logging.getLogger()


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def function_response_from_request(req: bytes):
    func = create_function_from_request_pdu(req[2:-2])
    if func.starting_address > 4000:
        ex_code = random.choice([1, 2, 3, 4, 5, 6])
        return struct.pack("<H", ex_code)

    slave_addr = req[1:2]
    res = b""
    if isinstance(func, ReadCoils):
        res = func.create_response_pdu(
            [random.randint(0, 255) for x in range(func.quantity)]
        )
    elif isinstance(func, ReadHoldingRegisters):
        res = func.create_response_pdu(
            [random.randint(0, 2**16 - 1) for x in range(func.quantity)]
        )
    elif isinstance(func, ReadInputRegisters):
        res = func.create_response_pdu(
            [random.randint(0, 2**16 - 1) for x in range(func.quantity)]
        )
    # Randomly inject Double CRC errors (see GH Issue #62)
    if random.choice([True, False]):
        return add_crc(add_crc(slave_addr + res))
    else:
        return add_crc(slave_addr + res)


class MockDatalogger(PySolarmanV5):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _socket_setup(self, *args, **kwargs):
        pass

    def v5_frame_response_encoder(self, modbus_frame):
        """Take a modbus RTU frame and encode it as a V5 data logging stick response frame

        :param modbus_frame: Modbus RTU frame
        :type modbus_frame: bytes
        :return: V5 frame
        :rtype: bytearray

        """
        length = 14 + len(modbus_frame)

        self.v5_length = struct.pack("<H", length)
        self.v5_seq = struct.pack(
            "<BB", self.sequence_number, self._get_next_sequence_number()
        )

        v5_header = self._v5_header(
            length, self._get_response_code(CONTROL_CODE.REQUEST), self.v5_seq
        )

        v5_payload = bytearray(
            self.v5_frametype
            + bytes.fromhex("01")
            + self.v5_deliverytime
            + self.v5_powerontime
            + self.v5_offsettime
            + modbus_frame
        )

        v5_frame = v5_header + v5_payload
        return v5_frame + self._v5_trailer(v5_frame)


class ServerHandler(socketserver.BaseRequestHandler):
    def setup(self, *args, **kwargs):
        self.sol = MockDatalogger(
            "0.0.0.0", 2612749371, socket="", auto_reconnect=False
        )
        self.count_packet = bytes.fromhex("a5010010478d69b5b50aa2006415")
        self.cl_packets = 0

    def handle(self) -> None:
        self.request: socket.socket
        while True:
            data = self.request.recv(1024)
            self.cl_packets += 1
            if self.cl_packets == 2:
                self.request.send(self.count_packet)
            if data == b"":
                break
            else:
                seq_no = data[5]
                self.sol.sequence_number = data[5]
                log.debug(f"[SrvHandler] RECD: {data}")
                data = bytearray(data)
                data[3] = 0x10
                data[4] = PySolarmanV5._get_response_code(CONTROL_CODE.REQUEST)
                try:
                    checksum = self.sol._calculate_v5_frame_checksum(bytes(data))
                except:
                    self.request.send(b"")
                    break
                data[-2:-1] = checksum.to_bytes(1, byteorder="big")
                data = bytes(data)
                log.debug(f"[SrvHandler] DEC: {data}")
                try:
                    decoded = self.sol._v5_frame_decoder(data)
                    enc = function_response_from_request(decoded)
                    log.debug(f'[SrvHandler] Generated Raw modbus: {enc.hex(" ")}')
                    enc = self.sol.v5_frame_response_encoder(enc)
                    log.debug(f'[SrvHandler] Sending frame: {bytes(enc).hex(" ")}')
                    self.request.send(bytes(enc))
                except Exception as e:
                    log.exception(e)
                    self.request.send(data)
                if self.cl_packets == 2:
                    # Uncomment for auto-reconnect tests
                    # It is unstable, tests can fail from time to time if enabled
                    # self.request.close()
                    # break
                    pass


async def random_delay():
    await asyncio.sleep(random.randint(10, 50) / 100)


async def stream_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Stream handler for the async test server

    :param reader:
    :param writer:
    :return:
    """
    sol = MockDatalogger("0.0.0.0", 2612749371, auto_reconnect=False)
    count_packet = bytes.fromhex("a5010010478d69b5b50aa2006415")
    non_v5_packet = bytes.fromhex(
        "41542b595a434d505645523d4d57335f3136555f353430365f322e32370d0a0d0a"
    )
    gibberish = bytes.fromhex("aa030a00000000000000000000be9c")
    more_gibberish = bytes.fromhex("0103080100020232333038c75c")
    cl_packets = 0

    while True:
        data = await reader.read(1024)
        cl_packets += 1
        if data == b"":
            break
        else:
            seq_no = data[5]
            sol.sequence_number = data[5]
            log.debug(f"[AioHandler] RECD: {data}")
            data = bytearray(data)
            data[3] = 0x10
            data[4] = PySolarmanV5._get_response_code(CONTROL_CODE.REQUEST)
            try:
                checksum = sol._calculate_v5_frame_checksum(bytes(data))
            except:
                writer.write(b"")
                await writer.drain()
                break
            data[-2:-1] = checksum.to_bytes(1, byteorder="big")
            data = bytes(data)
            log.debug(f"[AioHandler] DEC: {data}")
            if cl_packets == 4:
                log.debug("C == 4. Writing empty bytes... Expecting reconnect")
                writer.write(b"")
                try:
                    await writer.drain()
                    break
                except:
                    log.error("Connection closed......")
                    break
            try:
                decoded = sol._v5_frame_decoder(data)
                enc = function_response_from_request(decoded)
                log.debug(f'[AioHandler] Generated Raw modbus: {enc.hex(" ")}')
                enc = sol.v5_frame_response_encoder(enc)
                log.debug(f'[AioHandler] Sending frame: {bytes(enc).hex(" ")}')
                writer.write(bytes(enc))
                await writer.drain()
            except V5FrameError as e:
                """Close immediately - allows testing with wrong serial numbers, sequence numbers etc."""
                log.debug(
                    f"[AioHandler] V5FrameError({' '.join(e.args)}). Closing immediately... "
                )
                break
            except Exception as e:
                log.exception(e)
                writer.write(data)
            if cl_packets == 3:
                # Write counter packet and wait some time to be consumed
                await random_delay()
                writer.write(count_packet)
                await writer.drain()
                await random_delay()
                writer.write(gibberish)
                await writer.drain()
                await random_delay()
                writer.write(non_v5_packet)
                await writer.drain()
                await random_delay()
                writer.write(more_gibberish)
                await writer.drain()
                await random_delay()
    try:
        writer.write(b"")
        await writer.drain()
        writer.close()
    except:
        pass


class SolarmanServer(metaclass=_Singleton):
    """
    Sync version of the test server
    """

    def __init__(self, address, port):
        self.srv = socketserver.TCPServer((address, port), ServerHandler)
        self.srv.timeout = 2
        thr = threading.Thread(target=self.run, daemon=True)
        thr.start()

    def run(self):
        self.srv.serve_forever(2)


class AioSolarmanServer(metaclass=_Singleton):
    """
    Async version of the test server
    """

    def __init__(self, address, port):
        self.address = address
        self.port = port
        try:
            self.loop = asyncio.get_running_loop()
            self.loop.create_task(self.start_server())
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            thr = threading.Thread(target=self.sync_runner, daemon=True)
            thr.start()

    async def start_server(self):
        await asyncio.start_server(
            stream_handler,
            host=self.address,
            port=self.port,
            family=socket.AF_INET,
            reuse_address=True,
            reuse_port=False if _WIN_PLATFORM else True,
        )

    def sync_runner(self):
        self.loop.create_task(self.start_server())
        self.loop.run_forever()
