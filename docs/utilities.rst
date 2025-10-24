===================
Utilities
===================

Solarman TCP Proxy
^^^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-tcp-proxy -h
    usage: solarman tcp proxy [-h] [-b BIND] [-p PORT] -l LOGGER -s SERIAL

    A Modbus TCP Proxy for Solarman loggers

    options:
      -h, --help           show this help message and exit
      -b, --bind BIND      The address to listen on
      -p, --port PORT      The TCP port to listen on
      -l, --logger LOGGER  The IP address of the logger
      -s, --serial SERIAL  The serial number of the logger

Solarman RTU Proxy
^^^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-rtu-proxy -h
    usage: solarman rtu proxy [-h] [-b BIND] [-p PORT] -l LOGGER -s SERIAL

    A Modbus RTU over TCP Proxy for Solarman loggers

    options:
      -h, --help           show this help message and exit
      -b, --bind BIND      The address to listen on
      -p, --port PORT      The TCP port to listen on
      -l, --logger LOGGER  The IP address of the logger
      -s, --serial SERIAL  The serial number of the logger

Solarman Scan Utility
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-scan -h
    usage: solarman-scan [-h] broadcast

    Scanner for IGEN/Solarman dataloggers

    positional arguments:
      broadcast   Network broadcast address

    options:
      -h, --help  show this help message and exit

Solarman Unicast Scanner
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-uni-scan wlan0

Solarman Decoder
^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-decoder -h
    usage: solarman-decoder [-h] frame_hex [frame_hex ...]

    Decode a Solarman V5 frame

    positional arguments:
      frame_hex   The bytes of the frame to decode in hexadecimal format e.g. a5 17 ...

    options:
      -h, --help  show this help message and exit
