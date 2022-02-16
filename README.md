# pysolarmanv5

This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
inverter data loggers. Modbus RTU frames can be encapsulated in the proprietary
Solarman v5 protocol and requests sent to the data logger on port tcp/8899.

This module aims to simplify the Solarman v5 protocol, exposing interfaces
similar to that of the uModbus library.

pysolarmanv5 supports the following Modbus RTU Function Codes:
|Modbus Function Code|Modbus Function Description|Width|Read/Write|pysolarmanv5 Function|
|---|---|---|---|---|
|1|Read Coils|1 bit|Read|[read_coils(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L263)
|2|Read Discrete Inputs|1 bit|Read|[read_discrete_inputs(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L269)
|3|Read Holding Registers|16 bits|Read|[read_holding_registers(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L241)
|4|Read Input Registers|16 bits|Read|[read_input_registers(register_addr, quantity)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L235)
|5|Write Single Coil|1 bit|Write|[write_single_coil(register_addr, value)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L277)
|6|Write Single Holding Register|16 bits|Write|[write_holding_register(register_addr, value)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L247)|
|16|Write Multiple Holding Registers|16 bits|Write|[write_multiple_holding_registers(register_addr, values)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L255)|
|N/A|Send Raw Modbus Frame|||[send_raw_modbus_frame(mb_request_frame)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L286)|
|N/A|Send Raw Modbus Frame With Parsed Reply|||[send_raw_modbus_frame_parsed(mb_request_frame)](https://github.com/jmccrohan/pysolarmanv5/blob/v2.3.0/pysolarmanv5/pysolarmanv5.py#L293)|

Details of the Solarman v5 protocol have been based on the excellent work of
[Inverter-Data-Logger by XtheOne](https://github.com/XtheOne/Inverter-Data-Logger/)
and others.

## Dependencies

pysolarmanv5 requires Python 3.8 or greater. pysolarmanv5 depends on [uModbus](https://github.com/AdvancedClimateSystems/uModbus).

## Installation

### PyPI

`pip install pysolarmanv5`

### Manual installation

- `git clone https://github.com/jmccrohan/pysolarmanv5.git`
- `cd pysolarmanv5`
- `pip install .`
- See example code in `examples`

## Contributions

Contributions welcome. Please raise any Issues / Pull Requests via [Github](https://github.com/jmccrohan/pysolarmanv5).

## License

pysolarmanv5 is licensed under the [MIT License](https://github.com/jmccrohan/pysolarmanv5/blob/master/LICENSE). Copyright (c) 2021 Jonathan McCrohan
