Solarman V5 Protocol
====================

**Solarman V5** is a proprietary protocol used by Solarman (IGEN-Tech) solar
inverter data loggers. Solarman V5 is TCP-based, and is used by the data loggers
for communicating both locally and with Solarman Cloud. Solarman data loggers
use Hi-Flying HF-A11 SOCs which by default use port tcp/8899.

By sending a suitably formed packet to the data logging stick on this port, one
can send and receive Modbus RTU frames directly to/from the inverter on port
tcp/8899 without interfering with Solarman Cloud operations.

.. note::
   This information has been gathered from various internet sources and from
   reverse engineered packet captures. No warranty/liability of any kind is
   provided.

For the purposes of this implementation, the Solarman V5 frame is composed of
three parts:

* :ref:`Header`
* :ref:`Payload` (incorporating Modbus RTU Frame)
* :ref:`Trailer`

All Solarman V5 fields are encoded Little Endian, with the exception of the Modbus
RTU frame, which is encoded Big Endian (as per Modbus spec).

Header
^^^^^^

The Header is always 11 bytes and is composed of:

* **Start** (*one byte*) – Denotes the start of the V5 frame. Always ``0xA5``.
* **Length** (*two bytes*) – :ref:`Payload` length
* **Control Code** (*two bytes*) – Describes the type of V5 frame:

  * HANDSHAKE ``0x4110``, used for initial handshake in server mode
  * DATA ``0x4210``, used for sending data in server mode
  * INFO ``0x4310``, used for sending stick fw, ip and ssid info in server mode
  * REQUEST ``0x4510``, for Modbus RTU requests in client mode

    * RESPONSE ``0x1510``, for Modbus RTU responses in client mode
  * HEARTBEAT ``0x4710``, keepalive packets in both modes
  * *REPORT* ``0x4810``
  *Responses are described as* ``request code - 0x3000`` *which can be seen in
  Modbus RTU response - request pair:* ``0x4510 - 0x3000 = 0x1510``
* **Sequence Number** (*two bytes*) – This field acts as a two-way sequence number. On
  outgoing requests, the first byte of this field is echoed back in the same
  position on incoming responses. pysolarmanv5 expoits this property to detect
  invalid responses. This is done by initialising this byte to a random value,
  and incrementing for each subsequent request.
  The second byte is incremented by the data logging stick for every response
  sent (either to Solarman Cloud or local requests).
* **Logger Serial Number** (*four bytes*) – Serial number of data logging stick

Payload
^^^^^^^
The Payload fields vary slightly between request and response frames. The size
of the Payload will also vary depending on the size of the embedded Modbus RTU
frame.

Request Payload
"""""""""""""""

A request payload is 15 bytes + the length of the Modbus RTU request frame, and
is composed of:

* **Frame Type** (*one byte*) – Denotes the frame type. pysolarmanv5 sets this
  to ``0x02`` on outgoing Modbus RTU requests, where ``0x02`` is understood to
  mean the solar inverter.
* **Sensor Type** (*two bytes*) – Denotes the sensor type. pysolarmanv5 sets
  this to ``0x0000`` on outgoing requests.
* **Total Working Time** (*four bytes*) – Denotes the frame total working time.
  See corresponding response field of same name for further details.
  pysolarmanv5 sets this to ``0x00000000`` on outgoing requests.
* **Power On Time** (*four bytes*) – Denotes the frame power on time. See
  corresponding response field of same name for further details. pysolarmanv5
  sets this to ``0x00000000`` on outgoing requests.
* **Offset Time** (*four bytes*) – Denotes the frame offset time. See
  corresponding response field of same name for further details. pysolarmanv5
  sets this to ``0x00000000`` on outgoing requests.
* **Modbus RTU Frame** (*variable length*) – Modbus RTU request frame.

Response Payload
""""""""""""""""
A response payload is 14 bytes + the length of the Modbus RTU response frame,
and is composed of:

* **Frame Type** (*one byte*) – Denotes the frame type, where:

  * ``0x02``: Solar Inverter
  * ``0x01``: Data Logging Stick
  * ``0x00``: Solarman Cloud (*or keep alive?*)
* **Status** (*one byte*) – Denotes the request status. ``0x01`` appears to
  denote real-time data.
* **Total Working Time** (*four bytes*) – Denotes the number of seconds that
  data logging stick has been operating. Other implementations have this
  field named *TimeOutOfFactory*.
* **Power On Time** (*four bytes*) – Denotes the current uptime of the data
  logging stick in seconds.
* **Offset Time** (*four bytes*) – Denotes offset timestamp, in seconds. This is
  defined as current data logging stick timestamp minus **Total Working Time**.
* **Modbus RTU Frame** (*variable length*) – Modbus RTU response frame. Some
  inverter/data logger combinations (DEYE + possibly others) exhibit a bug
  whereby the Modbus frame is suffixed with two addtional bytes. It is assumed
  that these devices are erroneously calculating and appending the Modbus CRC
  twice. This is effectively `one-pass CRC checking
  <https://en.wikipedia.org/wiki/Computation_of_cyclic_redundancy_checks#One-pass_checking>`_
  and as a result, the additional two bytes are always ``0x0000``. pysolarmanv5
  will transparently detect and correct this double CRC issue.

Response Timestamp Fields
"""""""""""""""""""""""""
The following statements in relation to the timestamp fields are true:

* **Total Working Time** minus **Power On Time** = Device Total Operation Time
  (as shown in Solarman Cloud).
* **Total Working Time** plus **Offset Time** = Data acquisition timestamp. By
  definition, pysolarmanv5 frames are real-time data frames, so this is
  equivalent to the current unix timestamp.

Trailer
^^^^^^^
The Trailer is always 2 bytes and is composed of:

* **Checksum** (*one byte*) – Denotes the V5 frame checksum. The checksum is
  computed on the entire V5 frame except for Start, Checksum (obviously!) and
  End.
  
  Note, that this field is completely separate to the Modbus RTU checksum, which
  coincidentally, is the two bytes immediately preceding this field.
* **End** (*one byte*) – Denotes the end of the V5 frame. Always ``0x15``.



Frame Diagrams
^^^^^^^^^^^^^^

Frame diagrams for request and response frames are shown below. Any values shown
below are in Network Byte Order.

.. todo::
   Figure out how to invert the colours of the SVG packet diagrams upon toggling
   furo's light/dark themes using custom CSS/JS.

   The current hack of duplicating each diagram for light and dark themes is
   not ideal, but options are limited because packetdiag doesn't support :class:
   directive.

Request Frame Format
""""""""""""""""""""
..
   Request Frame packetdiag is duplicated below. Only difference is the
   default_linecolor and default_textcolor values. Used for Furo's dark and
   light themes respectively.

.. container:: only-dark

	.. packetdiag::

	    packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = white
	      default_textcolor = white
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x1045)\n(2 bytes)
	      40-55: Sequence Number (0xAA00)\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x2)\n(1 byte)
	      96-111: Sensor Type (0x0000)\n(2 bytes)
	      112-143: Total Working Time (0x00000000)\n(4 bytes)
	      144-175: Power On Time (0x00000000)\n(4 bytes)
	      176-207: Offset Time (0x00000000)\n(4 bytes)
	      208-271: Modbus RTU Frame\n(variable bytes)
	      272-279: Checksum\n(1 byte)
	      280-287: End (0x15)\n(1 byte)
	   }

.. container:: only-light

	.. packetdiag::

	    packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = black
	      default_textcolor = black
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x1045)\n(2 bytes)
	      40-55: Sequence Number (0xAA00)\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x2)\n(1 byte)
	      96-111: Sensor Type (0x0000)\n(2 bytes)
	      112-143: Total Working Time (0x00000000)\n(4 bytes)
	      144-175: Power On Time (0x00000000)\n(4 bytes)
	      176-207: Offset Time (0x00000000)\n(4 bytes)
	      208-271: Modbus RTU Frame\n(variable bytes)
	      272-279: Checksum\n(1 byte)
	      280-287: End (0x15)\n(1 byte)
	   }

Response Frame Format
"""""""""""""""""""""
..
   Response Frame packetdiag is duplicated below. Only difference is the
   default_linecolor and default_textcolor values. Used for Furo's dark and
   light themes respectively.

.. container:: only-dark

	.. packetdiag::

	    packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = white
	      default_textcolor = white
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x1015)\n(2 bytes)
	      40-55: Sequence Number (0xAA00)\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x02)\n(1 byte)
	      96-103: Status (0x01)\n(1 byte)
	      104-135: Total Working Time\n(4 bytes)
	      136-167: Power On Time\n(4 bytes)
	      168-199: Offset Time\n(4 bytes)
	      200-255: Modbus RTU Frame\n(variable bytes)
	      256-263: Checksum\n(1 byte)
	      264-271: End (0x15)\n(1 byte)
	   }

.. container:: only-light

	.. packetdiag::

	    packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = black
	      default_textcolor = black
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x1015)\n(2 bytes)
	      40-55: Sequence Number (0xAA00)\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x02)\n(1 byte)
	      96-103: Status (0x01)\n(1 byte)
	      104-135: Total Working Time\n(4 bytes)
	      136-167: Power On Time\n(4 bytes)
	      168-199: Offset Time\n(4 bytes)
	      200-255: Modbus RTU Frame\n(variable bytes)
	      256-263: Checksum\n(1 byte)
	      264-271: End (0x15)\n(1 byte)
	   }

Response Frame Format (Server)
""""""""""""""""""""""""""""""
.. container:: only-dark

    .. packetdiag::

        packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = white
	      default_textcolor = white
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x10XX)\n(2 bytes)
	      40-55: Sequence Number\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x02)\n(1 byte)
	      96-103: Status (0x01)\n(1 byte)
	      104-135: UNIX Timestamp\n(4 bytes)
	      136-167: TZ Offset (in minutes)\n(4 bytes)
	      168-175: V5 checksum\n(1 byte)
	      176-183: End (0x15)\n(1 byte)
	   }

.. container:: only-light

    .. packetdiag::

        packetdiag {
	      colwidth = 32
	      scale_interval = 8
	      node_height = 32
	      default_node_color = none
	      default_linecolor = black
	      default_textcolor = black
	      default_fontsize = 10

	      0-7: Start (0xA5)\n(1 byte)
	      8-23: Length\n(2 bytes)
	      24-39: Control Code (0x10XX)\n(2 bytes)
	      40-55: Sequence Number\n(2 bytes)
	      56-87: Logger Serial Number\n(4 bytes)
	      88-95: Frame Type (0x02)\n(1 byte)
	      96-103: Status (0x01)\n(1 byte)
	      104-135: UNIX Timestamp\n(4 bytes)
	      136-167: TZ Offset (in minutes)\n(4 bytes)
	      168-175: V5 checksum\n(1 byte)
	      176-183: End (0x15)\n(1 byte)
	   }


Further reading
^^^^^^^^^^^^^^^
For further information on the Solarman V5 Protocol, see the following:

* ``com.igen.xiaomaizhidian`` APK (see ``src/java/com/igen/*``)
* https://github.com/XtheOne/Inverter-Data-Logger/issues/3#issuecomment-878911661
* https://github.com/XtheOne/Inverter-Data-Logger/blob/Experimental_Frame_Version_5_support/InverterLib.py#L48
