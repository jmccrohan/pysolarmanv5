# Changelog

## [v2.3.0] - 2022-02-02

### Changed

- Improve V5 Frame documentation

### Fixed

- Removed erroneous shebang on pysolarmanv5.py
- Fix traceback with write_holding_register() (See GH issue #2)

## [v2.2.0] - 2022-01-15

### Added

- Added dependencies on Python 3.8 and uModbus
- Implement Modbus Function Codes 01, 02 and 05

### Changed

- Remove binascii methods

### Fixed

- V5 Frame validation added in v2.1.0 corrected

## [v2.1.0] - 2022-01-04

### Changed

- Add more robust validation for V5 frame replies

## [v2.0.1] - 2021-12-29

### Added

- Add write_multiple_holding_registers() - function code 16

### Changed

- Minor typo fixes

## [v2.0.0] - 2021-11-25

### Added

- Updated examples

### Changed

- Changed the return type of read_input_registers() and read_holding_registers()
  from an int to a list of ints.
- The previous functionality is now provided by read_input_register_formatted()
  and read_holding_register_formatted()

### Fixed

- Bitshift and bitmask parameters now work correctly

## [v1.0.0] - 2021-11-25

### Added

- Initial commit
