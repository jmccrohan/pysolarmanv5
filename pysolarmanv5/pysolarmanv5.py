"""pysolarmanv5.py"""

import time
import errno
import queue
import types
import struct
import socket
import logging
import platform
import selectors

from threading import Thread, Event
from multiprocessing import Queue
from typing import Any
from random import randrange

from umodbus.client.serial import rtu
from umodbus.client.serial.redundancy_check import get_crc
from umodbus.exceptions import error_code_to_exception_map


_WIN_PLATFORM = platform.system() == "Windows"


CONTROL_CODE = types.SimpleNamespace()
CONTROL_CODE.HANDSHAKE = 0x41
CONTROL_CODE.DATA = 0x42
CONTROL_CODE.INFO = 0x43
CONTROL_CODE.REQUEST = 0x45
CONTROL_CODE.HEARTBEAT = 0x47
CONTROL_CODE.REPORT = 0x48


class V5FrameError(Exception):
    """V5 Frame Validation Error"""


class NoSocketAvailableError(Exception):
    """No Socket Available Error"""


# pylint: disable-next=too-many-instance-attributes (R0902)
class PySolarmanV5:
    """
    The PySolarmanV5 class establishes a TCP connection to a Solarman V5 data
    logging stick and exposes methods to send/receive Modbus RTU requests and
    responses.

    For more detailed information on the Solarman V5 Protocol, see
    :doc:`solarmanv5_protocol`

    :param address: IP address or hostname of data logging stick
    :type address: str
    :param serial: Serial number of the data logging stick (not inverter!)
    :type serial: int
    :param port: TCP port to connect to data logging stick, defaults to 8899
    :type port: int, optional
    :param mb_slave_id: Inverter Modbus slave ID, defaults to 1
    :type mb_slave_id: int, optional
    :param socket_timeout: Socket timeout duration in seconds, defaults to 60
    :type socket_timeout: int, optional
    :param v5_error_correction: Enable naive error correction for V5 frames,
        defaults to False
    :type v5_error_correction: bool, optional

    .. versionadded:: v2.4.0

    :param logger: Python logging facility
    :type logger: Logger, optional
    :param socket: TCP Socket connection to data logging stick. If **socket**
        argument is provided, **address** argument is unused (however, it is
        still required as a positional argument)
    :type socket: Socket, optional
    :raises NoSocketAvailableError: If no network socket is available

    .. versionadded:: v2.5.0

    :param auto_reconnect: Activates the auto-reconnect functionality.
        PySolarmanV5 will try to keep the connection open. The default is False.
        Not compatible with custom sockets.
    :type auto_reconnect: Boolean, optional

    .. deprecated:: v2.4.0

    :param verbose: Enable verbose logging, defaults to False. Use **logger**
        instead. For compatibility purposes, **verbose**, if enabled, will
        create a logger, and set the logging level to DEBUG.
    :type verbose: bool, optional

    Basic example:
       >>> from pysolarmanv5 import PySolarmanV5
       >>> modbus = PySolarmanV5("192.168.1.10", 123456789)
       >>> print(modbus.read_input_registers(register_addr=33022, quantity=6))

    See :doc:`examples` directory for further examples.

    """

    def __init__(self, address, serial, **kwargs):
        """Constructor"""

        self.log = kwargs.get("logger", None)
        if self.log is None:
            logging.basicConfig()
            self.log = logging.getLogger(__name__)

        self.address = address
        self.serial = serial

        self.port = kwargs.get("port", 8899)
        self.mb_slave_id = kwargs.get("mb_slave_id", 1)
        self.verbose = kwargs.get("verbose", False)
        self.socket_timeout = kwargs.get("socket_timeout", 60)
        self.v5_error_correction = kwargs.get("v5_error_correction", False)
        self.sequence_number = None

        if self.verbose:
            self.log.setLevel("DEBUG")

        # Define and construct V5 request frame structure.
        self.v5_start = bytes.fromhex("A5")
        self.v5_length = bytes.fromhex("0000")  # placeholder value
        self.v5_control_codes = CONTROL_CODE.__dict__.values()
        self.v5_control_code_suffix = bytes.fromhex("10")
        self.v5_seq = bytes.fromhex("0000")  # placeholder value
        self.v5_serial = struct.pack("<I", self.serial)
        self.v5_frametype = bytes.fromhex("02")
        self.v5_sensortype = bytes.fromhex("0000")
        self.v5_deliverytime = bytes.fromhex("00000000")
        self.v5_powerontime = bytes.fromhex("00000000")
        self.v5_offsettime = bytes.fromhex("00000000")
        self.v5_checksum = bytes.fromhex("00")  # placeholder value
        self.v5_end = bytes.fromhex("15")

        self.sock: socket.socket = None  # noqa
        self._poll: selectors.BaseSelector = None  # noqa
        self._sock_fd: int = None  # noqa
        self._auto_reconnect = False
        self._data_queue: Queue = None  # noqa
        self._data_wanted: Event = None  # noqa
        self._reader_exit: Event = None  # noqa
        self._reader_thr: Thread = None  # noqa
        self._last_frame: bytes = b""
        self._socket_setup(kwargs.get("socket"), kwargs.get("auto_reconnect", False))

    @staticmethod
    def _get_response_code(code: int) -> int:
        """
        Get response control code from request control code

        :param code: V5 request control code
        :type code: int
        :return: V5 response control code
        :rtype: int

        """
        return code - 0x30

    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum on all bytes

        :param data: data for checksum calculation
        :type data: bytes
        :return: Checksum value of all bytes
        :rtype: int

        """
        checksum = 0
        for d in data:
            checksum += d & 0xFF
        return int(checksum & 0xFF)

    @staticmethod
    def _calculate_v5_frame_checksum(frame: bytes) -> int:
        """
        Calculate checksum on all frame bytes except head, end and checksum

        :param frame: V5 frame for checksum calculation
        :type frame: bytes
        :return: Checksum value of V5 frame
        :rtype: int

        """
        return PySolarmanV5._calculate_checksum(frame[1:-2])

    def _v5_header(self, length: int, control: int, seq: bytes) -> bytearray:
        """
        Construct V5 header

        :param length: V5 frame length
        :type length: int
        :param control: V5 control code
        :type control: int
        :param seq: V5 sequence number
        :type seq: bytes
        :return: V5 frame header
        :rtype: bytearray

        """
        return bytearray(
            self.v5_start
            + struct.pack("<H", length)
            + self.v5_control_code_suffix
            + struct.pack("<B", control)
            + seq
            + self.v5_serial
        )

    def _v5_trailer(self, data: bytes) -> bytearray:
        """
        Construct V5 trailer

        :param data: data for checksum calculation
        :type data: bytes
        :return: V5 frame trailer
        :rtype: bytearray

        """
        return bytearray(
            struct.pack("<B", self._calculate_checksum(data[1:])) + self.v5_end
        )

    def _get_next_sequence_number(self) -> int:
        """
        Get the next sequence number for use in outgoing packets

        If ``sequence_number`` is None, generate a random int as initial value.

        :return: Sequence number
        :rtype: int

        """
        if self.sequence_number is None:
            self.sequence_number = randrange(0x01, 0xFF)
        else:
            self.sequence_number = (self.sequence_number + 1) & 0xFF
        return self.sequence_number

    def _v5_frame_encoder(self, modbus_frame: bytes) -> bytearray:
        """
        Take a modbus RTU frame and encode it in a V5 data logging stick frame

        :param modbus_frame: Modbus RTU frame
        :type modbus_frame: bytes
        :return: V5 frame
        :rtype: bytearray

        """
        length = 15 + len(modbus_frame)

        self.v5_length = struct.pack("<H", length)
        self.v5_seq = struct.pack("<H", self._get_next_sequence_number())

        v5_header = self._v5_header(length, CONTROL_CODE.REQUEST, self.v5_seq)

        v5_payload = bytearray(
            self.v5_frametype
            + self.v5_sensortype
            + self.v5_deliverytime
            + self.v5_powerontime
            + self.v5_offsettime
            + modbus_frame
        )

        v5_frame = v5_header + v5_payload
        return v5_frame + self._v5_trailer(v5_frame)

    def _v5_frame_decoder(self, v5_frame: bytes) -> bytearray:
        """
        Decodes a V5 data logging stick frame and returns a modbus RTU frame

        Modbus RTU frame will start at position 25 through ``len(v5_frame)-2``.

        Occasionally logger can send a spurious 'keep-alive' reply with a
        control code of ``0x4710``. These messages can either take the place of,
        or be appended to valid ``0x1510`` responses. In this case, the v5_frame
        will contain an invalid checksum.

        Validate the following:

        1) V5 start and end are correct (``0xA5`` and ``0x15`` respectively)
        2) V5 checksum is correct
        3) V5 outgoing sequence number has been echoed back to us (byte 5)
        4) V5 data logger serial number is correct (in most (all?) instances the
           reply is correct, but request can obviously be incorrect)
        5) V5 control code is correct (``0x1510``)
        6) v5_frametype contains the correct value (``0x02`` in byte 11)
        7) Modbus RTU frame length is at least 5 bytes (vast majority of RTU
           frames will be >=6 bytes, but valid 5 byte error/exception RTU frames
           are possible)

        :param v5_frame: V5 frame
        :type v5_frame: bytes
        :return: Modbus RTU Frame
        :rtype: bytes
        :raises V5FrameError: If parsing fails due to invalid V5 frame

        """
        frame_len = len(v5_frame)
        (payload_len,) = struct.unpack("<H", v5_frame[1:3])

        frame_len_without_payload_len = 13

        if frame_len != (frame_len_without_payload_len + payload_len):
            self.log.debug("frame_len does not match payload_len.")
            if self.v5_error_correction:
                frame_len = frame_len_without_payload_len + payload_len

        if (v5_frame[0] != int.from_bytes(self.v5_start, byteorder="big")) or (
            v5_frame[-1] != int.from_bytes(self.v5_end, byteorder="big")
        ):
            raise V5FrameError("V5 frame contains invalid start or end values")
        if v5_frame[-2] != self._calculate_v5_frame_checksum(v5_frame):
            raise V5FrameError("V5 frame contains invalid V5 checksum")
        if v5_frame[5] != self.sequence_number:
            raise V5FrameError("V5 frame contains invalid sequence number")
        if v5_frame[7:11] != self.v5_serial:
            raise V5FrameError("V5 frame contains incorrect data logger serial number")
        if v5_frame[4] != self._get_response_code(CONTROL_CODE.REQUEST):
            raise V5FrameError("V5 frame contains incorrect control code")
        if v5_frame[11] != int("02", 16):
            raise V5FrameError("V5 frame contains invalid frametype")

        modbus_frame = v5_frame[25:-2]

        if len(modbus_frame) < 5:
            if len(modbus_frame) > 0 and (
                err := error_code_to_exception_map.get(modbus_frame[0])
            ):
                raise V5FrameError(f"V5 Modbus EXCEPTION: {err.__name__}")
            raise V5FrameError("V5 frame does not contain a valid Modbus RTU frame")

        return modbus_frame

    def _v5_time_response_frame(self, frame: bytes) -> bytearray:
        """
        Creates time response frame

        :param frame: V5 request frame
        :type frame: bytes
        :return: V5 time response frame
        :rtype: bytearray

        """
        response_frame = self._v5_header(
            10, self._get_response_code(frame[4]), frame[5:7]
        ) + bytearray(
            +struct.pack("<H", 0x0100)  # Frame & sensor type?
            + struct.pack("<I", int(time.time()))
            + struct.pack("<I", 0)  # Offset?
        )
        response_frame[5] = (response_frame[5] + 1) & 0xFF
        return response_frame + self._v5_trailer(response_frame)

    def _send_receive_frame(self, frame: bytes) -> bytes:
        """
        Send frame to the data logger and receive response

        :param frame: Frame to transmit
        :type frame: bytes
        :return: Received frame
        :rtype: bytes
        :raises NoSocketAvailableError: When the connection to data logger is closed.
            Can occur even when auto-reconnect is enabled.

        """
        self.log.debug("[%s] SENT: %s", self.serial, frame.hex(" "))
        if not self._reader_thr.is_alive():
            raise NoSocketAvailableError("Connection already closed.")
        self.sock.sendall(frame)
        self._data_wanted.set()
        self._last_frame = frame
        response_frame = b""
        try:
            response_frame = self._data_queue.get(timeout=self.socket_timeout)
            if response_frame == b"":
                raise NoSocketAvailableError("Connection closed on read")
            self._data_wanted.clear()
        except (queue.Empty, TimeoutError):
            self.log.debug("Got exception when receiving frame", exc_info=True)
            raise
        except OSError as exc:
            self.log.debug("Got exception when receiving frame", exc_info=True)
            if exc.errno == errno.EHOSTUNREACH:
                raise TimeoutError from exc
            raise

        self.log.debug("[%s] RECD: %s", self.serial, response_frame.hex(" "))
        return response_frame

    def _received_frame_is_valid(self, frame: bytes) -> bool:
        """
        Check that the frame is valid and that the serial number of the received
        frame matches with the last sent one

        :param frame: V5 request frame
        :type frame: bytes
        :return: Is valid V5 frame?
        :rtype: bool

        """
        if not frame.startswith(self.v5_start):
            self.log.debug("[%s] V5_MISMATCH: %s", self.serial, frame.hex(" "))
            return False
        if frame[5] != self.sequence_number:
            self.log.debug("[%s] V5_SEQ_NO_MISMATCH: %s", self.serial, frame.hex(" "))
            return False
        return True

    def _received_frame_response(self, frame: bytes) -> tuple[bool, bytearray]:
        """
        Return response to frames with control codes 0x41 (handshake), 0x42 (data), 0x43 (info), 0x47 (heartbeat) and 0x48 (report)

        :param frame: V5 request frame
        :type frame: bytes
        :return: Continue processing frame?, V5 time response frame
        :rtype: tuple[bool, bytearray]

        """
        do_continue = True
        response_frame = None
        if frame[4] != CONTROL_CODE.REQUEST and frame[4] in self.v5_control_codes:
            do_continue = False
            # Maybe do_continue = True for CONTROL_CODE.DATA|INFO|REPORT and thus process packets in the future?
            control_name = [
                i for i in CONTROL_CODE.__dict__ if CONTROL_CODE.__dict__[i] == frame[4]
            ][0]
            self.log.debug("[%s] V5_%s: %s", self.serial, control_name, frame.hex(" "))
            response_frame = self._v5_time_response_frame(frame)
            self.log.debug(
                "[%s] V5_%s RESP: %s",
                self.serial,
                control_name,
                response_frame.hex(" "),
            )
        return do_continue, response_frame

    def _handle_protocol_frame(self, frame: bytes) -> bool:
        """
        Handles frames with known control codes :func:`_received_frame_response() <pysolarmanv5.PySolarmanV5._received_frame_response>`

        :param frame: V5 request frame
        :type frame: bytes
        :return: Continue processing frame?
        :rtype: bool

        """
        do_continue, response_frame = self._received_frame_response(frame)
        if response_frame is not None:
            if self._reader_thr.is_alive():
                self.sock.sendall(response_frame)
        return do_continue

    def _data_receiver(self):
        self._poll.register(self.sock.fileno(), selectors.EVENT_READ)
        while True:
            events = self._poll.select(0.500)
            if self._reader_exit.is_set():
                return
            # pylint: disable-next=unused-variable.
            for event in events:
                # We are registered only for inbound data on a single socket,
                # so there is no need to check the (fileno, mask) tuples
                try:
                    data = self.sock.recv(1024)
                except Exception:  # pylint: disable=broad-exception-caught
                    # In the case of errors (peer reset, timeout, ...) set received data to empty to signal receive failure
                    self.log.debug("[%s] Connection error", self.serial, exc_info=True)
                    data = b""
                if data == b"":
                    self.log.debug("[POLL] Socket closed. Reader thread exiting.")
                    if self._data_wanted.is_set():
                        self._reconnect()
                        if self.sock:
                            self.log.debug(
                                "[POLL] Data expected. Will retry the last request: %s",
                                self._last_frame.hex(" "),
                            )
                            self.sock.sendall(self._last_frame)
                            return
                        try:
                            self._data_queue.put_nowait(data)
                        except queue.Full:
                            pass
                    else:
                        self._reconnect()
                    return
                if not self._received_frame_is_valid(data):
                    continue
                if not self._handle_protocol_frame(data):
                    continue
                if self._data_wanted.is_set():
                    self._data_queue.put(data, timeout=self.socket_timeout)
                else:
                    self.log.debug("[POLL-DISCARDED] RECD: %s", data.hex(" "))

    def _reconnect(self):
        """
        Reconnect to the data logger if needed
        """

        # Close the old socket. Closing failures can be ignored and just logged.
        try:
            if self.sock:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
        except Exception:  # pylint: disable=broad-exception-caught
            self.log.debug("Closing socket failed", exc_info=True)
        finally:
            self.sock = None
            self._reader_exit.set()
        if self._auto_reconnect:
            self.log.debug(
                "Auto-Reconnect enabled. Trying to establish a new connection"
            )
            if self._sock_fd:
                self._poll.unregister(self._sock_fd)
                self._sock_fd = None
            self.sock = self._create_socket()
            if self.sock:
                self._sock_fd = self.sock.fileno()
                self._reader_exit.clear()
                self._reader_thr = Thread(target=self._data_receiver, daemon=True)
                self._reader_thr.start()
                self.log.debug("Auto-Reconnect successful.")
            else:
                self.log.debug("No socket available! Reconnect failed.")
                self.sock = None
        else:
            self.log.debug("Auto-Reconnect inactive.")
            self.sock = None

    def disconnect(self) -> None:
        """
        Disconnect the socket and set a signal for the reader thread to exit

        :return: None

        """
        self._data_wanted.clear()
        self._reader_exit.set()
        try:
            if self.sock:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
        except Exception:  # pylint: disable=broad-exception-caught
            self.log.debug("Closing socket failed", exc_info=True)
        finally:
            self.sock = None

        self._reader_thr.join(0.5)
        if self._sock_fd:
            self._poll.unregister(self._sock_fd)
            self._sock_fd = None

    def _send_receive_modbus_frame(self, mb_request_frame):
        """Encodes mb_frame, sends/receives v5_frame, decodes response

        :param mb_request_frame: Modbus RTU frame to transmit
        :type mb_request_frame: bytes
        :return: Modbus RTU frame received
        :rtype: bytes

        """
        v5_request_frame = self._v5_frame_encoder(mb_request_frame)
        v5_response_frame = self._send_receive_frame(v5_request_frame)
        mb_response_frame = self._v5_frame_decoder(v5_response_frame)
        return mb_response_frame

    def _handle_double_crc(self, frame: bytes) -> bytes:
        """
        Strip extra zeroes in case that the frame has double CRC applied

        .. note::
           See the discussion on `GitHub issue #62 <https://github.com/jmccrohan/pysolarmanv5/issues/62>`_
           for more info.

        :param frame: RTU response
        :return: modified (if necessary) RTU frame
        """

        zeroes = bytes.fromhex("0000")
        if not frame.endswith(zeroes):
            return frame
        stripped = frame[:-2]
        if get_crc(stripped[:-2]) == stripped[-2:]:
            return stripped
        return frame

    def _get_modbus_response(self, mb_request_frame):
        """Returns mb response values for a given mb_request_frame

        :param mb_request_frame: Modbus RTU frame to parse
        :type mb_request_frame: bytes
        :return: Modbus RTU decoded values
        :rtype: list[int]

        """
        mb_response_frame = self._send_receive_modbus_frame(mb_request_frame)
        try:
            modbus_values = rtu.parse_response_adu(mb_response_frame, mb_request_frame)
        except struct.error as e:
            response = self._handle_double_crc(mb_response_frame)
            if len(response) != len(mb_response_frame):
                modbus_values = rtu.parse_response_adu(response, mb_request_frame)
            else:
                raise e
        return modbus_values

    def _create_socket(self):
        """Creates and returns a socket"""
        try:
            sock = socket.create_connection(
                (self.address, self.port), self.socket_timeout
            )
        except OSError:
            self.log.debug("Socket creation failed", exc_info=True)
            return None
        return sock

    def _socket_setup(self, sock: Any, auto_reconnect: bool):
        """Socket setup method"""
        if isinstance(sock, socket.socket) or sock is None:
            self.sock = sock if sock else self._create_socket()
            if self.sock is None:
                raise NoSocketAvailableError("No socket available")
            if _WIN_PLATFORM:
                self._poll = selectors.DefaultSelector()
            else:
                self._poll = selectors.PollSelector()
            self._sock_fd = self.sock.fileno()
            self._auto_reconnect = False if sock else auto_reconnect
            self._data_queue = Queue(maxsize=1)
            self._data_wanted = Event()
            self._reader_exit = Event()
            self._reader_thr = Thread(target=self._data_receiver, daemon=True)
            self._reader_thr.start()
            self.log.debug("Socket setup completed... %s", self.sock)

    @staticmethod
    def twos_complement(val, num_bits):
        """Calculate 2s Complement

        :param val: Value to calculate
        :type val: int
        :param num_bits: Number of bits
        :type num_bits: int

        :return: 2s Complement value
        :rtype: int

        """
        if val < 0:
            val = (1 << num_bits) + val
        else:
            if val & (1 << (num_bits - 1)):
                val = val - (1 << num_bits)
        return val

    def _format_response(self, modbus_values, **kwargs):
        """Formats a list of modbus register values (16 bits each) as a single value

        :param modbus_values: Modbus register values
        :type modbus_values: list[int]
        :param scale: Scaling factor
        :type scale: int
        :param signed: Signed value (2s complement)
        :type signed: bool
        :param bitmask: Bitmask value
        :type bitmask: int
        :param bitshift: Bitshift value
        :type bitshift: int
        :return: Formatted register value
        :rtype: int

        """
        scale = kwargs.get("scale", 1)
        signed = kwargs.get("signed", False)
        bitmask = kwargs.get("bitmask", None)
        bitshift = kwargs.get("bitshift", None)
        response = 0
        num_registers = len(modbus_values)

        for i, j in zip(range(num_registers), range(num_registers - 1, -1, -1)):
            response += modbus_values[i] << (j * 16)
        if signed:
            response = self.twos_complement(response, num_registers * 16)
        if scale != 1:
            response *= scale
        if bitmask is not None:
            response &= bitmask
        if bitshift is not None:
            response >>= bitshift

        return response

    def read_input_registers(self, register_addr, quantity):
        """Read input registers from modbus slave (Modbus function code 4)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int

        :return: List containing register values
        :rtype: list[int]

        """
        mb_request_frame = rtu.read_input_registers(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_holding_registers(self, register_addr, quantity):
        """Read holding registers from modbus slave (Modbus function code 3)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int

        :return: List containing register values
        :rtype: list[int]

        """
        mb_request_frame = rtu.read_holding_registers(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_input_register_formatted(self, register_addr, quantity, **kwargs):
        """Read input registers from modbus slave and format as single value (Modbus function code 4)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int
        :param scale: Scaling factor
        :type scale: int
        :param signed: Signed value (2s complement)
        :type signed: bool
        :param bitmask: Bitmask value
        :type bitmask: int
        :param bitshift: Bitshift value
        :type bitshift: int
        :return: Formatted register value
        :rtype: int

        """
        modbus_values = self.read_input_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def read_holding_register_formatted(self, register_addr, quantity, **kwargs):
        """Read holding registers from modbus slave and format as single value (Modbus function code 3)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int
        :param scale: Scaling factor
        :type scale: int
        :param signed: Signed value (2s complement)
        :type signed: bool
        :param bitmask: Bitmask value
        :type bitmask: int
        :param bitshift: Bitshift value
        :type bitshift: int
        :return: Formatted register value
        :rtype: int

        """
        modbus_values = self.read_holding_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def write_holding_register(self, register_addr, value):
        """Write a single holding register to modbus slave (Modbus function code 6)

        :param register_addr: Modbus register address
        :type register_addr: int
        :param value: value to write
        :type value: int
        :return: value written
        :rtype: int

        """
        mb_request_frame = rtu.write_single_register(
            self.mb_slave_id, register_addr, value
        )
        value = self._get_modbus_response(mb_request_frame)
        return value

    def write_multiple_holding_registers(self, register_addr, values):
        """Write list of multiple values to series of holding registers on modbus slave (Modbus function code 16)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param values: values to write
        :type values: list[int]
        :return: values written
        :rtype: list[int]

        """
        mb_request_frame = rtu.write_multiple_registers(
            self.mb_slave_id, register_addr, values
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_coils(self, register_addr, quantity):
        """Read coils from modbus slave and return list of coil values (Modbus function code 1)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int
        :return: register values
        :rtype: list[int]

        """
        mb_request_frame = rtu.read_coils(self.mb_slave_id, register_addr, quantity)
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_discrete_inputs(self, register_addr, quantity):
        """Read discrete inputs from modbus slave and return list of input values (Modbus function code 2)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int
        :return: register values
        :rtype: list[int]

        """
        mb_request_frame = rtu.read_discrete_inputs(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def write_single_coil(self, register_addr, value):
        """Write single coil value to modbus slave (Modbus function code 5)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param value: value to write; ``0xFF00`` (On) or ``0x0000`` (Off)
        :type value: int
        :return: value written
        :rtype: int

        """
        mb_request_frame = rtu.write_single_coil(self.mb_slave_id, register_addr, value)
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def write_multiple_coils(self, register_addr, values):
        """Write multiple coil values to modbus slave (Modbus function code 15)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param values: values to write; ``1`` (On) or ``0`` (Off)
        :type values: list[int]
        :return: values written
        :rtype: list[int]

        """
        mb_request_frame = rtu.write_multiple_coils(
            self.mb_slave_id, register_addr, values
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def masked_write_holding_register(self, register_addr, **kwargs):
        """Mask write a single holding register to modbus slave (Modbus function code 22)

        Used to set or clear individual bits within a holding register

        If default values are provided for both ``or_mask`` and ``and_mask``,
        the write element of this function is a NOP.

        .. warning::
           This is not implemented as a native Modbus function. It is a software
           implementation using a combination of :func:`read_holding_registers() <pysolarmanv5.PySolarmanV5.read_holding_registers>`
           and :func:`write_holding_register() <pysolarmanv5.PySolarmanV5.write_holding_register>`.

           It is therefore **not atomic**.

        :param register_addr: Modbus register address
        :type register_addr: int
        :param or_mask: OR mask (set bits), defaults to ``0x0000`` (no change)
        :type or_mask: int
        :param and_mask: AND mask (clear bits), defaults to ``0xFFFF`` (no change)
        :type and_mask: int
        :return: value written
        :rtype: int

        """
        or_mask = kwargs.get("or_mask", 0x0000)
        and_mask = kwargs.get("and_mask", 0xFFFF)

        current_value = self.read_holding_registers(register_addr, 1)[0]

        if (or_mask != 0x0000) or (and_mask != 0xFFFF):
            masked_value = current_value
            masked_value |= or_mask
            masked_value &= and_mask
            updated_value = self.write_holding_register(register_addr, masked_value)
            return updated_value
        return current_value

    def send_raw_modbus_frame(self, mb_request_frame):
        """Send raw modbus frame and return modbus response frame

        Wrapper around internal method :func:`_send_receive_modbus_frame() <pysolarmanv5.PySolarmanV5._send_receive_modbus_frame>`

        :param mb_request_frame: Modbus frame
        :type mb_request_frame: bytearray
        :return: Modbus frame
        :rtype: bytearray

        """
        return self._send_receive_modbus_frame(mb_request_frame)

    def send_raw_modbus_frame_parsed(self, mb_request_frame):
        """Send raw modbus frame and return parsed modbusresponse list

        Wrapper around internal method :func:`_get_modbus_response() <pysolarmanv5.PySolarmanV5._get_modbus_response>`

        :param mb_request_frame: Modbus frame
        :type mb_request_frame: bytearray
        :return: Modbus RTU decoded values
        :rtype: list[int]
        """
        return self._get_modbus_response(mb_request_frame)
