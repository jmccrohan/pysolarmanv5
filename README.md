# pysolarmanv5

This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
inverter data loggers. Modbus RTU frames can be encapsulated in the proprietary
Solarman v5 protocol and requests sent to the data logger on port tcp/8899.

This module aims to simplify the Solarman v5 protocol, exposing interfaces
similar to that of the [uModbus](https://pysolarmanv5.readthedocs.io/) library.

Details of the Solarman v5 protocol have been based on the excellent work of
[Inverter-Data-Logger by XtheOne](https://github.com/XtheOne/Inverter-Data-Logger/)
and others.

## Documentation

pysolarmanv5 documentation is available on [Read the Docs](https://pysolarmanv5.readthedocs.io/).

The Solarman V5 protocol is documented [here](https://pysolarmanv5.readthedocs.io/en/latest/solarmanv5_protocol.html).

## Supported Devices

A user contributed list of supported devices is available [here](https://github.com/jmccrohan/pysolarmanv5/issues/11).

If you are unsure if your device is supported, please use the [solarman_scan](https://github.com/jmccrohan/pysolarmanv5/blob/main/utils/solarman_scan.py) 
utility to find compatible data logging sticks on your local network.

Please note that the **Solis S3-WIFI-ST** data logging stick is **NOT supported**.  
See [GH issue #8](https://github.com/jmccrohan/pysolarmanv5/issues/8) for further information. 

Some Ethernet data logging sticks have native support Modbus TCP and therefore **do not require pysolarmanv5**.
See [GH issue #5](https://github.com/jmccrohan/pysolarmanv5/issues/5) for further information. 

## Dependencies

- pysolarmanv5 requires Python 3.8 or greater.
- pysolarmanv5 depends on [uModbus](https://github.com/AdvancedClimateSystems/uModbus).

## Installation

To install the latest stable version of pysolarmanv5 from PyPi, run:

`pip install pysolarmanv5`

To install the latest development version from git, run:

`pip install git+https://github.com/jmccrohan/pysolarmanv5.git`

## Projects using pysolarmanv5

- [NosIreland/solismon3](https://github.com/NosIreland/solismon3)
- [NosIreland/solismod](https://github.com/NosIreland/solismod)
- [jmccrohan/ha_pyscript_pysolarmanv5](https://github.com/jmccrohan/ha_pyscript_pysolarmanv5)
- [YodaDaCoda/hass-solarman-modbus](https://github.com/YodaDaCoda/hass-solarman-modbus)
- [schwatter/solarman_mqtt](https://github.com/schwatter/solarman_mqtt)
- [RonnyKempe/solismon](https://github.com/RonnyKempe/solismon)
- [toledobastos/solarman_battery_autocharge](https://github.com/toledobastos/solarman_battery_autocharge)
- [AndyTaylorTweet/solis2mqtt](https://github.com/AndyTaylorTweet/solis2mqtt)
- [pixellos/codereinvented.automation.py](https://github.com/pixellos/codereinvented.automation.py)
- [cjgwhite/hass-solar](https://github.com/cjgwhite/hass-solar)
- [imcfarla2003/solarconfig](https://github.com/imcfarla2003/solarconfig)
- [githubDante/deye-controller](https://github.com/githubDante/deye-controller)

## Contributions

Contributions welcome. Please raise any Issues / Pull Requests via [Github](https://github.com/jmccrohan/pysolarmanv5).

## License

pysolarmanv5 is licensed under the [MIT License](https://github.com/jmccrohan/pysolarmanv5/blob/master/LICENSE). Copyright (c) 2022 Jonathan McCrohan
