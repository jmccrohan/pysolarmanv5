"""Scan Modbus registers to find valid registers"""

from pysolarmanv5 import PySolarmanV5, V5FrameError
import umodbus.exceptions


def main():
    modbus = PySolarmanV5(
        "192.168.1.24", 123456789, port=8899, mb_slave_id=1, verbose=False
    )

    print("Scanning input registers")
    for x in range(30000, 39999):
        try:
            val = modbus.read_input_registers(register_addr=x, quantity=1)[0]
            print(f"Register: {x:05}\t\tValue: {val:05} ({val:#06x})")
        except (V5FrameError, umodbus.exceptions.IllegalDataAddressError):
            continue
    print("Finished scanning input registers")

    print("Scanning holding registers")
    for x in range(40000, 49999):
        try:
            val = modbus.read_holding_registers(register_addr=x, quantity=1)[0]
            print(f"Register: {x:05}\t\tValue: {val:05} ({val:#06x})")
        except (V5FrameError, umodbus.exceptions.IllegalDataAddressError):
            continue
    print("Finished scanning holding registers")


if __name__ == "__main__":
    main()
