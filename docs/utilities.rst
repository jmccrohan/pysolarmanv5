===================
Utilities
===================


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

    user@host:~ $ solarman-scan

Solarman Unicast Scanner
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-uni-scan wlan0

Solarman Decoder
^^^^^^^^^^^^^^^^

.. code-block:: console

    user@host:~ $ solarman-decoder
