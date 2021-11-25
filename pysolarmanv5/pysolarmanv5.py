#!/usr/bin/env python3
"""pysolarmanv5.py"""
import struct
import socket
import binascii

from umodbus.client.serial import rtu

class PySolarmanV5:
    """
    pysolarmanv5.py

    This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
    inverter data loggers. Modbus RTU frames can be encapsulated in the
    proprietary Solarman v5 protocol and requests sent to the data logger on
    port tcp/8899.

    This module aims to simplfy the Solarman v5 protocol, exposing interfaces
    similar to that of the uModbus library.
    """
    def __init__(self, address, serial, **kwargs):
        """Constructor. Requires address and serial number of data logger as
        required parameters. Optional parameters are port, modbus slave id,
        socket timeout, and log verbosity
        """

        self.address = address
        self.serial = serial

        self.port = kwargs.get('port', 8899)
        self.mb_slave_id = kwargs.get('mb_slave_id', 1)
        self.verbose = kwargs.get('verbose', 0)
        self.socket_timeout = kwargs.get('socket_timeout', 60)

        self._v5_frame_def()
        self.sock = self._create_socket()

    def _v5_frame_def(self):
        """Define the V5 data logger frame structure.
        
        start + length + controlcode + serial + loggerserial + datafield +
        modbus_frame + checksum + end

        v5_loggerserial contains the data logger serial number (hex'd and reversed)
        v5_checksum contains a dummy value of 0x00. The actual value is
        calculated once the frame is constructed (see _calculate_v5_frame_checksum())

        For further information on the v5 frame structure, see:
        https://github.com/XtheOne/Inverter-Data-Logger/issues/3#issuecomment-878911661
        https://github.com/XtheOne/Inverter-Data-Logger/blob/Experimental_Frame_Version_5_support/InverterLib.py#L48
        """
        self.v5_start = binascii.unhexlify('A5')
        self.v5_length = binascii.unhexlify('1700')
        self.v5_controlcode = binascii.unhexlify('1045')
        self.v5_serial = binascii.unhexlify('0000')
        self.v5_loggerserial = struct.unpack('>I',struct.pack('<I',
            int(self.serial)))[0].to_bytes(4,byteorder='big')
        self.v5_datafield = binascii.unhexlify('020000000000000000000000000000')
        self.v5_checksum = binascii.unhexlify('00')
        self.v5_end = binascii.unhexlify('15') # Logger End code

    @staticmethod
    def _calculate_v5_frame_checksum(frame):
        """Calculate checksum on all frame bytes except head, end and checksum"""
        checksum = 0
        for i in range(1, len(frame) - 2, 1):
            checksum += frame[i] & 0xFF
        return int((checksum & 0xFF))

    def _v5_frame_encoder(self,modbus_frame):
        """Take a modbus RTU frame and encode it in a V5 data logging stick frame"""
        v5_frame = bytearray(self.v5_start + self.v5_length
                + self.v5_controlcode + self.v5_serial
                + self.v5_loggerserial + self.v5_datafield + modbus_frame
                + self.v5_checksum + self.v5_end)
        v5_frame[len(v5_frame) - 2] = self._calculate_v5_frame_checksum(v5_frame)
        return v5_frame

    def _v5_frame_decoder(self,v5_frame):
        """Decodes a V5 data logging stick frame and returns a modbus RTU frame

        Validate the head, checksum and end values

        Modbus RTU frame will start at position 25 through len(v5_frame)-2
        """

        frame_len = len(v5_frame)
        if ((bytes([v5_frame[0]]) != self.v5_start)
                or (bytes([v5_frame[frame_len - 1]]) != self.v5_end)
                or (v5_frame[frame_len - 2] != self._calculate_v5_frame_checksum(v5_frame))):
            raise V5FrameError("Error decoding V5 frame")

        modbus_frame = v5_frame[25:frame_len-2]
        return modbus_frame

    def _send_receive_v5_frame(self,data_logging_stick_frame):
        """Send v5 frame to the data logger and receive response"""
        if self.verbose==1:
            print("SENT: "+str(binascii.hexlify(data_logging_stick_frame, b' ')))

        self.sock.sendall(data_logging_stick_frame)
        data = self.sock.recv(1024)

        if self.verbose==1:
            print("RECD: " + str(binascii.hexlify(data, b' ')))
        return data

    def _send_receive_modbus_frame(self, mb_request_frame):
        """Encodes mb_frame, sends/receives v5_frame, decodes response"""
        v5_request_frame = self._v5_frame_encoder(mb_request_frame)
        v5_response_frame = self._send_receive_v5_frame(v5_request_frame)
        mb_response_frame = self._v5_frame_decoder(v5_response_frame)
        return mb_response_frame

    def _get_modbus_response(self, mb_request_frame):
        """Returns mb response values for a given mb_request_frame"""
        mb_response_frame = self._send_receive_modbus_frame(mb_request_frame)
        modbus_values = rtu.parse_response_adu(mb_response_frame,mb_request_frame)
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
            if val & (1 << (num_bits -1)):
                val = val - (1 << num_bits)
        return val

    def _format_response(self, modbus_values, **kwargs):
        """Formats a list of modbus register values (16 bits each) as a single value"""
        scale = kwargs.get('scale', 1)
        signed = kwargs.get('signed', 0)
        bitmask = kwargs.get('bitmask', None)
        bitshift = kwargs.get('bitshift', None)
        response = 0
        num_registers = len(modbus_values)

        for i,j in zip(range(num_registers),range(num_registers - 1, -1, -1)) :
            response += modbus_values[i] << (j * 16)

        if signed:
            response = self.twos_complement(response, num_registers * 16)

        response *= scale

        if bitmask is not None:
            response &= bitmask

        if bitshift is not None:
            response >>= bitshift
        
        return response

    def read_input_registers(self, register_addr, quantity, **kwargs):
        """Read input registers from modbus slave and return value (Modbus function code 0x4)"""
        mb_request_frame = rtu.read_input_registers(self.mb_slave_id, register_addr, quantity)
        modbus_values = self._get_modbus_response(mb_request_frame)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def read_holding_registers(self, register_addr, quantity, **kwargs):
        """Read holding registers from modbus slave and return value (Modbus function code 0x3)"""
        mb_request_frame = rtu.read_holding_registers(self.mb_slave_id, register_addr, quantity)
        modbus_values = self._get_modbus_response(mb_request_frame)
        value = self._format_response(modbus_values, **kwargs)
        return value

    def write_holding_register(self, register_addr, value, **kwargs):
        """Write a single holding register to modbus slave (Modbus function code 0x6)"""
        mb_request_frame = rtu.write_single_register(self.mb_slave_id, register_addr, value)
        modbus_values = self._get_modbus_response(mb_request_frame)
        value = self._format_response(modbus_values, **kwargs)
        return value
