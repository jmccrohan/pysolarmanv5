pysolarmanv5
============

.. toctree::
   :maxdepth: 2
   :hidden:

   API Reference <api_reference>
   solarmanv5_protocol
   examples
   utilities

.. toctree::
   :caption: Project Links
   :hidden:

   changelog
   GitHub <https://github.com/jmccrohan/pysolarmanv5>
   PyPI <https://pypi.org/project/pysolarmanv5>
   Read the Docs <https://pysolarmanv5.readthedocs.io/>

**pysolarmanv5** is a Python module to interact with Solarman (IGEN-Tech) v5
based solar inverter data loggers. Modbus RTU frames can be encapsulated in the
proprietary Solarman v5 protocol and requests sent to the data logger on port
tcp/8899. This module aims to simplify the Solarman v5 protocol, exposing
interfaces similar to that of the
`uModbus <https://github.com/AdvancedClimateSystems/uModbus>`_ library.

pysolarmanv5 supports the following Modbus RTU function codes:

.. list-table::
   :header-rows: 1

   * - Modbus Function Code
     - Modbus Function Description
     - Width
     - R/W
     - pysolarmanv5 Function(s)
   * - 1
     - Read Coils
     - 1 bit
     - Read
     - | :func:`read_coils() <pysolarmanv5.PySolarmanV5.read_coils>`
   * - 2
     - Read Discrete Inputs
     - 1 bit
     - Read
     - | :func:`read_discrete_inputs() <pysolarmanv5.PySolarmanV5.read_discrete_inputs>`
   * - 3
     - Read Holding Registers
     - 16 bits
     - Read
     - | :func:`read_holding_registers() <pysolarmanv5.PySolarmanV5.read_holding_registers>`
       | :func:`read_holding_register_formatted() <pysolarmanv5.PySolarmanV5.read_holding_register_formatted>`
   * - 4
     - Read Input Registers
     - 16 bits
     - Read
     - | :func:`read_input_registers() <pysolarmanv5.PySolarmanV5.read_input_registers>`
       | :func:`read_input_register_formatted() <pysolarmanv5.PySolarmanV5.read_input_register_formatted>`
   * - 5
     - Write Single Coil
     - 1 bit
     - Write
     - | :func:`write_single_coil() <pysolarmanv5.PySolarmanV5.write_single_coil>`
   * - 6
     - Write Single Holding Register
     - 16 bits
     - Write
     - | :func:`write_holding_register() <pysolarmanv5.PySolarmanV5.write_holding_register>`
   * - 15
     - Write Multiple Coils
     - 1 bit
     - Write
     - :func:`write_multiple_coils() <pysolarmanv5.PySolarmanV5.write_multiple_coils>`
   * - 16
     - Write Multiple Holding Registers
     - 16 bits
     - Write
     - :func:`write_multiple_holding_registers() <pysolarmanv5.PySolarmanV5.write_multiple_holding_registers>`
   * - 22 (:func:`see note <pysolarmanv5.PySolarmanV5.masked_write_holding_register>`)
     - Masked Write Register
     - 16 bits
     - Write
     - | :func:`masked_write_holding_register() <pysolarmanv5.PySolarmanV5.masked_write_holding_register>`
   * - N/A
     - Send Raw Modbus Frame
     - N/A
     - N/A
     - | :func:`send_raw_modbus_frame() <pysolarmanv5.PySolarmanV5.send_raw_modbus_frame>`
       | :func:`send_raw_modbus_frame_parsed() <pysolarmanv5.PySolarmanV5.send_raw_modbus_frame_parsed>`

..

Dependencies
------------
* pysolarmanv5 requires Python 3.8 or greater.
* pysolarmanv5 depends on `uModbus <https://github.com/AdvancedClimateSystems/uModbus>`_.

Installation
------------

To install the latest stable version of pysolarmanv5 from PyPi, run:

   pip install pysolarmanv5

To install the latest development version from git, run:

   pip install git+https://github.com/jmccrohan/pysolarmanv5.git

Contributions
-------------
Contributions welcome. Please raise any Issues / Pull Requests via
`GitHub <https://github.com/jmccrohan/pysolarmanv5>`_.

License
-------
pysolarmanv5 is licensed under the `MIT License <https://github.com/jmccrohan/pysolarmanv5/blob/main/LICENSE>`_.
