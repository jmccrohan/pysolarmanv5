"""pysolarmanv5.py"""
import struct
import socket

from umodbus.client.serial import rtu


class V5FrameError(Exception):
    pass


class PySolarmanV5:
    """
    pysolarmanv5.py

    This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
    inverter data loggers. Modbus RTU frames can be encapsulated in the
    proprietary Solarman v5 protocol and requests sent to the data logger on
    port tcp/8899.

    This module aims to simplify the Solarman v5 protocol, exposing interfaces
    similar to that of the uModbus library.
    """

    def __init__(self, address, serial, **kwargs):
        """Constructor. Requires address and serial number of data logger as
        required parameters. Optional parameters are port, modbus slave id,
        socket timeout, and log verbosity
        """

        self.address = address
        self.serial = serial

        self.port = kwargs.get("port", 8899)
        self.mb_slave_id = kwargs.get("mb_slave_id", 1)
        self.verbose = kwargs.get("verbose", 0)
        self.socket_timeout = kwargs.get("socket_timeout", 60)

        self._v5_frame_def()
        self.sock = self._create_socket()

    def _v5_frame_def(self):
        """Define the V5 data logger request frame structure.

        +--+----+----+----+--------+--+----+--------+--------+--------+----------------+--+--+
        |A5|1700|1045|0000|12345678|02|0000|00000000|00000000|00000000|0103A802000105AA|FF|15|
        ++-+--+-+--+-+-+--+--+-----++-+-+--+-+------+-+------+-+------+----+-----------++-+-++
        ||    |    |   |     |      |   |    |        |        |           |            |   ||
        |v    |    |   v     |      v   |    v        |        v           v            |   v|
        |Start|    |  Serial |    Frame |  Delivery   |       Offset    Modbus RTU      | End|
        |     v    |         v    Type  |  Time       v       Time      Frame           |    |
        |   Length |       Logger       v           PowerOn                             v    |
        |          v       Serial      Sensor       Time                             Checksum|
        |        Control               Type                                                  |
        |        Code                                                                        |
        +------------------------------------------------------------------------------------+

        - v5_length contains the payload size (little endian unsigned short).
          Set as a dummy value of 0x0000 below. Length calculated as part of
          _v5_frame_encoder()
        - payload is defined as:
            v5_frametype + v5_sensortype + v5_deliverytime + v5_powerontime +
            v5_offsettime + modbus_frame
        - v5_loggerserial contains the data logger serial number (little endian
          unsigned long)
        - v5_checksum contains a dummy value of 0x00. The actual value is
          calculated once the frame is constructed (see _calculate_v5_frame_checksum())

        For further information on the v5 frame structure, see:
        com.igen.xiaomaizhidian APK (src/java/com/igen/*)
        https://github.com/XtheOne/Inverter-Data-Logger/issues/3#issuecomment-878911661
        https://github.com/XtheOne/Inverter-Data-Logger/blob/Experimental_Frame_Version_5_support/InverterLib.py#L48
        """
        self.v5_start = bytes.fromhex("A5")
        self.v5_length = bytes.fromhex("0000")  # placeholder value
        self.v5_controlcode = bytes.fromhex("1045")
        self.v5_serial = bytes.fromhex("0000")
        self.v5_loggerserial = struct.pack("<I", self.serial)
        self.v5_frametype = bytes.fromhex("02")
        self.v5_sensortype = bytes.fromhex("0000")
        self.v5_deliverytime = bytes.fromhex("00000000")
        self.v5_powerontime = bytes.fromhex("00000000")
        self.v5_offsettime = bytes.fromhex("00000000")
        self.v5_checksum = bytes.fromhex("00")  # placeholder value
        self.v5_end = bytes.fromhex("15")

    @staticmethod
    def _calculate_v5_frame_checksum(frame):
        """Calculate checksum on all frame bytes except head, end and checksum"""
        checksum = 0
        for i in range(1, len(frame) - 2, 1):
            checksum += frame[i] & 0xFF
        return int((checksum & 0xFF))

    def _v5_frame_encoder(self, modbus_frame):
        """Take a modbus RTU frame and encode it in a V5 data logging stick frame"""

        self.v5_length = struct.pack("<H", 15 + len(modbus_frame))

        v5_frame = bytearray(
            self.v5_start
            + self.v5_length
            + self.v5_controlcode
            + self.v5_serial
            + self.v5_loggerserial
            + self.v5_frametype
            + self.v5_sensortype
            + self.v5_deliverytime
            + self.v5_powerontime
            + self.v5_offsettime
            + modbus_frame
            + self.v5_checksum
            + self.v5_end
        )
        v5_frame[len(v5_frame) - 2] = self._calculate_v5_frame_checksum(v5_frame)
        return v5_frame

    def _v5_frame_decoder(self, v5_frame):
        """Decodes a V5 data logging stick frame and returns a modbus RTU frame

        Modbus RTU frame will start at position 25 through len(v5_frame)-2

        Validate the following:
        1) V5 header and trailer are correct (0xA5 and 0x15 respectively)
        2) V5 checksum is correct
        3) V5 data logger serial number is correct (in most (all?) instances the
           reply is correct, but request is incorrect)
        4) V5 control code is correct (0x1015); Logger ocassionally sends
           spurious replies with 0x1047 control codes
        5) v5_frametype contains the correct value (0x02 in byte 11)
        6) Modbus RTU frame length is at least 5 bytes (vast majority of RTU
           frames will be >=6 bytes, but valid 5 byte error/exception RTU frames
           are possible)
        """
        frame_len = len(v5_frame)

        if (v5_frame[0] != int.from_bytes(self.v5_start, byteorder="big")) or (
            v5_frame[frame_len - 1] != int.from_bytes(self.v5_end, byteorder="big")
        ):
            raise V5FrameError("V5 frame contains invalid header or trailer values")
        if v5_frame[frame_len - 2] != self._calculate_v5_frame_checksum(v5_frame):
            raise V5FrameError("V5 frame contains invalid V5 checksum")
        if v5_frame[7:11] != self.v5_loggerserial:
            raise V5FrameError("V5 frame contains incorrect data logger serial number")
        if v5_frame[3:5] != bytes.fromhex("1015"):
            raise V5FrameError("V5 frame contains incorrect control code")
        if v5_frame[11] != int("02", 16):
            raise V5FrameError("V5 frame contains invalid datafield prefix")

        modbus_frame = v5_frame[25 : frame_len - 2]

        if len(modbus_frame) < 5:
            raise V5FrameError("V5 frame does not contain a valid Modbus RTU frame")

        return modbus_frame

    def _send_receive_v5_frame(self, data_logging_stick_frame):
        """Send v5 frame to the data logger and receive response"""
        if self.verbose == 1:
            print("SENT: " + data_logging_stick_frame.hex(" "))

        self.sock.sendall(data_logging_stick_frame)
        v5_response = self.sock.recv(1024)

        if self.verbose == 1:
            print("RECD: " + v5_response.hex(" "))
        return v5_response

    def _send_receive_modbus_frame(self, mb_request_frame):
        """Encodes mb_frame, sends/receives v5_frame, decodes response"""
        v5_request_frame = self._v5_frame_encoder(mb_request_frame)
        v5_response_frame = self._send_receive_v5_frame(v5_request_frame)
        mb_response_frame = self._v5_frame_decoder(v5_response_frame)
        return mb_response_frame

    def _get_modbus_response(self, mb_request_frame):
        """Returns mb response values for a given mb_request_frame"""
        mb_response_frame = self._send_receive_modbus_frame(mb_request_frame)
        modbus_values = rtu.parse_response_adu(mb_response_frame, mb_request_frame)
        return modbus_values

    def _create_socket(self):
        """Creates and returns a socket"""
        sock = socket.create_connection((self.address, self.port), self.socket_timeout)
        return sock

    @staticmethod
    def twos_complement(val, num_bits):
        """Calculate 2s Complement"""
        if val < 0:
            val = (1 << num_bits) + val
        else:
            if val & (1 << (num_bits - 1)):
                val = val - (1 << num_bits)
        return val

    def _format_response(self, modbus_values, **kwargs):
        """Formats a list of modbus register values (16 bits each) as a single value"""
        scale = kwargs.get("scale", 1)
        signed = kwargs.get("signed", 0)
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
        """Read input registers from modbus slave and return list of register values (Modbus function code 4)"""
        mb_request_frame = rtu.read_input_registers(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_holding_registers(self, register_addr, quantity):
        """Read holding registers from modbus slave and return list of register values (Modbus function code 3)"""
        mb_request_frame = rtu.read_holding_registers(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_input_register_formatted(self, register_addr, quantity, **kwargs):
        """Read input registers from modbus slave and return single value (Modbus function code 4)"""
        modbus_values = self.read_input_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def read_holding_register_formatted(self, register_addr, quantity, **kwargs):
        """Read holding registers from modbus slave and return single value (Modbus function code 3)"""
        modbus_values = self.read_holding_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def write_holding_register(self, register_addr, value, **kwargs):
        """Write a single holding register to modbus slave (Modbus function code 6)"""
        mb_request_frame = rtu.write_single_register(
            self.mb_slave_id, register_addr, value
        )
        value = self._get_modbus_response(mb_request_frame)
        return value

    def write_multiple_holding_registers(self, register_addr, values):
        """Write list of multiple values to series of holding registers to modbus slave (Modbus function code 16)"""
        mb_request_frame = rtu.write_multiple_registers(
            self.mb_slave_id, register_addr, values
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_coils(self, register_addr, quantity):
        """Read coils from modbus slave and return list of coil values (Modbus function code 1)"""
        mb_request_frame = rtu.read_coils(self.mb_slave_id, register_addr, quantity)
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def read_discrete_inputs(self, register_addr, quantity):
        """Read discrete inputs from modbus slave and return list of input values (Modbus function code 2)"""
        mb_request_frame = rtu.read_discrete_inputs(
            self.mb_slave_id, register_addr, quantity
        )
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def write_single_coil(self, register_addr, value):
        """Write single coil value to modbus slave (Modbus function code 5)

        Only valid values are 0xFF00 (On) and 0x0000 (Off)
        """
        mb_request_frame = rtu.write_single_coil(self.mb_slave_id, register_addr, value)
        modbus_values = self._get_modbus_response(mb_request_frame)
        return modbus_values

    def send_raw_modbus_frame(self, mb_request_frame):
        """Send raw modbus frame and return modbus response frame

        Wrapper for internal method _send_receive_modbus_frame()
        """
        return self._send_receive_modbus_frame(mb_request_frame)

    def send_raw_modbus_frame_parsed(self, mb_request_frame):
        """Send raw modbus frame and return parsed modbusresponse list

        Wrapper around internal method _get_modbus_response()
        """
        return self._get_modbus_response(mb_request_frame)
