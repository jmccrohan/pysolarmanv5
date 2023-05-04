import socket
import threading

from pysolarmanv5 import PySolarmanV5
import struct
from umodbus.client.serial.redundancy_check import add_crc
from umodbus.functions import (ReadHoldingRegisters, ReadInputRegisters, ReadCoils,
                               create_function_from_request_pdu)
import socketserver
import random
import logging

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
    slave_addr = req[1:2]
    res = b''
    if isinstance(func, ReadCoils):
        res = func.create_response_pdu([random.randint(0, 255) for x in range(func.quantity)])
    elif isinstance(func, ReadHoldingRegisters):
        res = func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])
    elif isinstance(func, ReadInputRegisters):
        res = func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])
    return add_crc(slave_addr + res)


class MockDatalogger(PySolarmanV5):

    def v5_frame_response_encoder(self, modbus_frame):
        """Take a modbus RTU frame and encode it as a V5 data logging stick response frame

        :param modbus_frame: Modbus RTU frame
        :type modbus_frame: bytes
        :return: V5 frame
        :rtype: bytearray

        """

        self.v5_length = struct.pack("<H", 15 + len(modbus_frame))
        self.v5_serial = struct.pack("<BB", self.sequence_number, self._get_next_sequence_number())
        v5_control = struct.pack("<H", 0x1510)

        v5_header = bytearray(
            self.v5_start
            + self.v5_length
            + v5_control
            + self.v5_serial
            + self.v5_loggerserial
        )

        v5_payload = bytearray(
            self.v5_frametype
            + bytes.fromhex('00')
            + self.v5_deliverytime
            + self.v5_powerontime
            + self.v5_offsettime
            + modbus_frame
        )

        v5_trailer = bytearray(self.v5_checksum + self.v5_end)
        v5_frame = v5_header + v5_payload + v5_trailer
        v5_frame[len(v5_frame) - 2] = self._calculate_v5_frame_checksum(v5_frame)
        return v5_frame


class ServerHandler(socketserver.BaseRequestHandler):

    def setup(self, *args, **kwargs):
        self.sol = MockDatalogger('0.0.0.0', 2612749371, socket='', auto_reconnect=False)
        self.count_packet = bytes.fromhex('a5010010478d69b5b50aa2006415')
        self.cl_packets = 0

    def handle(self) -> None:
        self.request: socket.socket
        while True:
            data = self.request.recv(1024)
            self.cl_packets += 1
            if self.cl_packets == 2:
                self.request.send(self.count_packet)
            if data == b'':
                break
            else:
                seq_no = data[5]
                self.sol.sequence_number = data[5]
                print('RECD: ', data)
                log.debug(f'[SrvHandler] RECD: {data}')
                data = bytearray(data)
                data[3:5] = struct.pack("<H", 0x1510)
                try:
                    checksum = self.sol._calculate_v5_frame_checksum(bytes(data))
                except:
                    self.request.send(b'')
                    break
                data[-2:-1] = checksum.to_bytes(1, byteorder='big')
                data = bytes(data)
                log.debug(f'[SrvHandler] DEC: {data}')
                try:
                    decoded = self.sol._v5_frame_decoder(data)
                    print(decoded)
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
                    #self.request.close()
                    #break
                    pass


class SolarmanServer(metaclass=_Singleton):

    def __init__(self, address, port):
        self.srv = socketserver.TCPServer((address, port), ServerHandler)
        self.srv.timeout = 2
        thr = threading.Thread(target=self.run, daemon=True)
        thr.start()

    def run(self):
        self.srv.serve_forever(2)
