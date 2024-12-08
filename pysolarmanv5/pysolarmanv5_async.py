"""pysolarmanv5_async.py"""

import errno
import asyncio
import struct

from multiprocessing import Event
from umodbus.client.serial import rtu

from .pysolarmanv5 import NoSocketAvailableError, PySolarmanV5

# Disable `invalid-overridden-method` rule. The class `PySolarmanV5Async` overrides
# (=redefines) non-async methods from `PySolarmanV5`.
# The override in this case is not a problem in practice.

# This could be avoided by changing the class hierarchy.
# One way would be to introduce a common base class for async and sync classes
# that would capture attributes and common (internal) sync methods.


# pylint: disable=invalid-overridden-method
class PySolarmanV5Async(PySolarmanV5):
    """
    The PySolarmanV5Async class establishes a TCP connection to a Solarman V5 data
    logging stick on a call to connect() and exposes methods to send/receive
    Modbus RTU requests and responses asynchronously.

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
    :param auto_reconnect: Auto reconnect to the data logging stick on error
    :type auto_reconnect: bool, optional

    Basic example:
       >>> import asyncio
       >>> from pysolarmanv5 import PySolarmanV5Async
       >>> modbus = PySolarmanV5Async("192.168.1.10", 123456789)
       >>> modbus2 = PySolarmanV5Async("192.168.1.11", 123456790)
       >>> loop = asyncio.get_event_loop()
       >>> loop.run_until_complete(asyncio.gather(*[modbus.connect(), modbus2.connect()], return_exceptions=True)
       >>>
       >>> print(loop.run_until_complete(modbus.read_input_registers(register_addr=33022, quantity=6)))
       >>> print(loop.run_until_complete(modbus2.read_input_registers(register_addr=33022, quantity=6)))

    See :doc:`examples` directory for further examples.

    """

    def __init__(self, address, serial, **kwargs):
        """Constructor"""
        super().__init__(address, serial, **kwargs)
        self._needs_reconnect = kwargs.get("auto_reconnect", False)
        """ Auto-reconnect feature """
        self.reader: asyncio.StreamReader = None  # noqa
        self.writer: asyncio.StreamWriter = None  # noqa
        self.data_queue = asyncio.Queue(maxsize=1)
        self.data_wanted_ev = Event()
        self.reader_task: asyncio.Task = None  # noqa

    async def connect(self) -> None:
        """
        Connect to the data logging stick and start the socket reader loop

        :return: None
        :raises NoSocketAvailableError: When connection cannot be established

        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.address, self.port), self.socket_timeout
            )
            loop = asyncio.get_running_loop()
            self.reader_task = loop.create_task(self._conn_keeper(), name="ConnKeeper")
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise NoSocketAvailableError(
                f"Cannot open connection to {self.address}"
            ) from e

    async def reconnect(self) -> None:
        """
        Reconnect to the data logging stick. Called automatically if the auto-reconnect option is enabled

        :return: None
        :raises NoSocketAvailableError: When connection cannot be re-established

        """
        try:
            if self.reader_task:
                self.reader_task.cancel()
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.address, self.port), self.socket_timeout
            )
            loop = asyncio.get_running_loop()
            self.reader_task = loop.create_task(self._conn_keeper(), name="ConnKeeper")
            self.log.debug("[%s] Successful reconnect", self.serial)
            if self.data_wanted_ev.is_set():
                self.log.debug(
                    "[%s] Data expected. Will retry the last request", self.serial
                )
                self.writer.write(self._last_frame)
                await self.writer.drain()
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.log.debug(  # pylint: disable=logging-fstring-interpolation
                f"Cannot open connection to {self.address}. [{type(e).__name__}{f': {e}' if f'{e}' else ''}]"
            )

    async def disconnect(self) -> None:
        """
        Disconnect the socket and set a signal for the reader thread to exit

        :return: None

        """
        if self.reader_task:
            self.reader_task.cancel()
        if self.writer:
            try:
                self.writer.write(b"")
                await self.writer.drain()
            except (AttributeError, ConnectionResetError) as e:
                self.log.debug(
                    f"{e} can be during closing ignored."
                )  # pylint: disable=logging-fstring-interpolation
            finally:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except OSError as e:  # Happens when host is unreachable.
                    self.log.debug(
                        f"{e} can be during closing ignored."
                    )  # pylint: disable=logging-fstring-interpolation

    def _socket_setup(self, *args, **kwargs):
        """Socket setup method

        PySolarmanV5Async handles socket creation separately to base
        PySolarmanV5 class

        """

    def _send_data(self, data: bytes):
        """
        Sends the data received from the socket to the receiver.

        :param data:
        :return:

        """
        if self.data_wanted_ev.is_set():
            if not self.data_queue.empty():
                _ = self.data_queue.get_nowait()
            self.data_queue.put_nowait(data)
            self.data_wanted_ev.clear()

    async def _conn_keeper(self) -> None:
        """
        Socket reader loop with extra logic when auto-reconnect is enabled

        :return: None

        """
        while True:
            try:
                data = await self.reader.read(1024)
            except ConnectionResetError:
                self.log.debug(
                    "[%s] Connection reset. Closing the socket reader.",
                    self.serial,
                    exc_info=True,
                )
                break
            if data == b"":
                self.log.debug(
                    "[%s] Connection closed by the remote. Closing the socket reader.",
                    self.serial,
                )
                break
            if not self._received_frame_is_valid(data):
                continue
            if self.data_wanted_ev.is_set():
                self._send_data(data)
            else:
                self.log.debug("Data received but nobody waits for it... Discarded")
        self.reader = None
        self.writer = None
        # self._send_data(b"")
        if self._needs_reconnect:
            self.log.debug(
                "[%s] Auto reconnect enabled. Will try to restart the socket reader",
                self.serial,
            )
            loop = asyncio.get_running_loop()
            loop.create_task(self.reconnect())

    async def _send_receive_v5_frame(self, data_logging_stick_frame):
        """Send v5 frame to the data logger and receive response

        :param data_logging_stick_frame: V5 frame to transmit
        :type data_logging_stick_frame: bytes
        :return: V5 frame received
        :rtype: bytes
        :raises NoSocketAvailableError: When the connection to data logging stick is closed.
            Can occur even when auto-reconnect is enabled.

        """
        self.log.debug("[%s] SENT: %s", self.serial, data_logging_stick_frame.hex(" "))
        self.data_wanted_ev.set()
        self._last_frame = data_logging_stick_frame
        try:
            self.writer.write(data_logging_stick_frame)
            await self.writer.drain()
            v5_response = await asyncio.wait_for(
                self.data_queue.get(), self.socket_timeout
            )
            if v5_response == b"":
                raise NoSocketAvailableError(
                    "Connection closed on read. Retry if auto-reconnect is enabled"
                )
        except AttributeError as exc:
            raise NoSocketAvailableError("Connection already closed") from exc
        except NoSocketAvailableError:
            raise
        except TimeoutError:
            raise
        except OSError as exc:
            if exc.errno == errno.EHOSTUNREACH:
                raise TimeoutError from exc
            raise
        except Exception as exc:
            self.log.exception("[%s] Send/Receive error: %s", self.serial, exc)
            raise
        finally:
            self.data_wanted_ev.clear()

        self.log.debug("[%s] RECD: %s", self.serial, v5_response.hex(" "))
        return v5_response

    async def _send_receive_modbus_frame(self, mb_request_frame):
        """Encodes mb_frame, sends/receives v5_frame, decodes response

        :param mb_request_frame: Modbus RTU frame to transmit
        :type mb_request_frame: bytes
        :return: Modbus RTU frame received
        :rtype: bytes

        """
        v5_request_frame = self._v5_frame_encoder(mb_request_frame)
        v5_response_frame = await self._send_receive_v5_frame(v5_request_frame)
        mb_response_frame = self._v5_frame_decoder(v5_response_frame)
        return mb_response_frame

    async def _get_modbus_response(self, mb_request_frame):
        """Returns mb response values for a given mb_request_frame

        :param mb_request_frame: Modbus RTU frame to parse
        :type mb_request_frame: bytes
        :return: Modbus RTU decoded values
        :rtype: list[int]

        """
        mb_response_frame = await self._send_receive_modbus_frame(mb_request_frame)
        try:
            modbus_values = rtu.parse_response_adu(mb_response_frame, mb_request_frame)
        except struct.error as e:
            response = self._handle_double_crc(mb_response_frame)
            if len(response) != len(mb_response_frame):
                modbus_values = rtu.parse_response_adu(response, mb_request_frame)
            else:
                raise e
        return modbus_values

    async def read_input_registers(self, register_addr, quantity):
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
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def read_holding_registers(self, register_addr, quantity):
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
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def read_input_register_formatted(self, register_addr, quantity, **kwargs):
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
        modbus_values = await self.read_input_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    async def read_holding_register_formatted(self, register_addr, quantity, **kwargs):
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
        modbus_values = await self.read_holding_registers(register_addr, quantity)
        value = self._format_response(modbus_values, **kwargs)
        return value

    async def write_holding_register(self, register_addr, value):
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
        value = await self._get_modbus_response(mb_request_frame)
        return value

    async def write_multiple_holding_registers(self, register_addr, values):
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
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def read_coils(self, register_addr, quantity):
        """Read coils from modbus slave and return list of coil values (Modbus function code 1)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param quantity: Number of registers to query
        :type quantity: int
        :return: register values
        :rtype: list[int]

        """
        mb_request_frame = rtu.read_coils(self.mb_slave_id, register_addr, quantity)
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def read_discrete_inputs(self, register_addr, quantity):
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
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def write_single_coil(self, register_addr, value):
        """Write single coil value to modbus slave (Modbus function code 5)

        :param register_addr: Modbus register start address
        :type register_addr: int
        :param value: value to write; ``0xFF00`` (On) or ``0x0000`` (Off)
        :type value: int
        :return: value written
        :rtype: int

        """
        mb_request_frame = rtu.write_single_coil(self.mb_slave_id, register_addr, value)
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def write_multiple_coils(self, register_addr, values):
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
        modbus_values = await self._get_modbus_response(mb_request_frame)
        return modbus_values

    async def masked_write_holding_register(self, register_addr, **kwargs):
        """Mask write a single holding register to modbus slave (Modbus function code 22)

        Used to set or clear individual bits within a holding register

        If default values are provided for both ``or_mask`` and ``and_mask``,
        the write element of this function is a NOP.

        .. warning::
           This is not implemented as a native Modbus function. It is a software
           implementation using a combination of :func:`read_holding_registers() <pysolarmanv5.PySolarmanV5Async.read_holding_registers>`
           and :func:`write_holding_register() <pysolarmanv5.PySolarmanV5Async.write_holding_register>`

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

        current_value = await self.read_holding_registers(register_addr, 1)[0]

        if (or_mask != 0x0000) or (and_mask != 0xFFFF):
            masked_value = current_value
            masked_value |= or_mask
            masked_value &= and_mask
            updated_value = await self.write_holding_register(
                register_addr, masked_value
            )
            return updated_value
        return current_value

    async def send_raw_modbus_frame(self, mb_request_frame):
        """Send raw modbus frame and return modbus response frame

        Wrapper around internal method :func:`_send_receive_modbus_frame() <pysolarmanv5.PySolarmanV5Async._send_receive_modbus_frame>`

        :param mb_request_frame: Modbus frame
        :type mb_request_frame: bytearray
        :return: Modbus frame
        :rtype: bytearray

        """
        return await self._send_receive_modbus_frame(mb_request_frame)

    async def send_raw_modbus_frame_parsed(self, mb_request_frame):
        """Send raw modbus frame and return parsed modbus response list

        Wrapper around internal method :func:`_get_modbus_response() <pysolarmanv5.PySolarmanV5Async._get_modbus_response>`

        :param mb_request_frame: Modbus frame
        :type mb_request_frame: bytearray
        :return: Modbus RTU decoded values
        :rtype: list[int]
        """
        return await self._get_modbus_response(mb_request_frame)
