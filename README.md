# pysolarmanv5

This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
inverter data loggers. Modbus RTU frames can be encapsulated in the proprietary
Solarman v5 protocol and requests sent to the data logger on port tcp/8899.

This module aims to simplify the Solarman v5 protocol, exposing interfaces
similar to that of the uModbus library.

The following Modbus RTU Function Codes are supported:
|Modbus Function Code|Description|pysolarmanv5 Function|
|---|---|---|
|3|Read Holding Registers|[read_holding_registers(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/f6f520f154c8ae3de372f94ca9246ef04556239a/pysolarmanv5/pysolarmanv5.py#L209)
|4|Read Input Registers|[read_input_registers(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/f6f520f154c8ae3de372f94ca9246ef04556239a/pysolarmanv5/pysolarmanv5.py#L201)
|6|Write Single Holding Register|[write_holding_register(register_addr, value)](https://github.com/jmccrohan/pysolarmanv5/blob/f6f520f154c8ae3de372f94ca9246ef04556239a/pysolarmanv5/pysolarmanv5.py#L229)|
|16|Write Multiple Holding Registers|[write_multiple_holding_registers(register_addr, values)](https://github.com/jmccrohan/pysolarmanv5/blob/f6f520f154c8ae3de372f94ca9246ef04556239a/pysolarmanv5/pysolarmanv5.py#L238)|

Details of the Solarman v5 protocol have been based on the excellent work of
[Inverter-Data-Logger by XtheOne](https://github.com/XtheOne/Inverter-Data-Logger/)
and others.

## Dependencies

pysolarmanv5 requires Python 3.8 or greater. pysolarmanv5 depends on [uModbus](https://github.com/AdvancedClimateSystems/uModbus).

## Installation

For the moment, run the steps below. I will publish to PyPI in due course.

- `git clone https://github.com/jmccrohan/pysolarmanv5.git`
- `cd pysolarmanv5`
- `pip install .`
- See example code in `examples`

## Contributions

Contributions welcome. Please raise any Issues / Pull Requests via [Github](https://github.com/jmccrohan/pysolarmanv5).

## License

pysolarmanv5 is licensed under the [MIT License](https://github.com/jmccrohan/pysolarmanv5/blob/master/LICENSE). Copyright (c) 2021 Jonathan McCrohan
