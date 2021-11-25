# pysolarmanv5

This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
inverter data loggers. Modbus RTU frames can be encapsulated in the proprietary
Solarman v5 protocol and requests sent to the data logger on port tcp/8899.

This module aims to simplfy the Solarman v5 protocol, exposing interfaces
similar to that of the uModbus library.

Details of the Solarman v5 protocol have been based on the excellent work of
[Inverter-Data-Logger by XtheOne](https://github.com/XtheOne/Inverter-Data-Logger/)
and others.

## Installation

For the moment, run the steps below. I will publish to PyPI in due course.

- `git clone https://github.com/jmccrohan/pysolarmanv5.git`
- `cd pysolarmanv5`
- `pip install .`
- See example code in `examples`
