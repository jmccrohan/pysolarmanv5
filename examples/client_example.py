""" A basic client demonstrating how to use pysolarmanv5."""
from pysolarmanv5.pysolarmanv5 import PySolarmanV5

def main():
    """Create new PySolarman instance, using IP address and S/N of data logger"""
    modbus = PySolarmanV5('192.168.1.24', 123456789, port = 8899, mb_slave_id = 1, verbose = 1)

    """Query two different input registers, of varying sizes"""
    print(modbus.read_input_registers(register_addr = 33022, quantity = 1))
    
    print(modbus.read_input_registers(register_addr = 33035, quantity = 1, scale = 0.1))
    
    print(modbus.read_input_registers(register_addr = 33079, quantity = 2,
        signed = 1))

    print(modbus.read_holding_registers(register_addr = 43000, quantity = 1))

if __name__ == "__main__":
    main()
