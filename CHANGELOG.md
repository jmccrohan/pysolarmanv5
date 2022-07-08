# Changelog

## [v2.4.0] - UNRELEASED

### Added

- Add [Sphinx/ReadTheDocs documentation](https://pysolarmanv5.readthedocs.io/)
- Add link to user-contributed list of supported data loggers/devices
  [See GH issue #11](https://github.com/jmccrohan/pysolarmanv5/issues/11)
- Add solarman_scan utility
- Add error_correction mode
- Implement Modbus Function Codes 15 and 22:
  write_multiple_coils()
  masked_write_holding_register()

### Changed

- Tidy up pysolarmanv5 namespace;
  Move PySolarmanV5 class from pysolarmanv5.pysolarmanv5 to pysolarmanv5
- Changed constructor parameters from int to bool where appropriate;
  Maintains backwards compatibility
- Properly implement Logging. Old verbose parameter marked as deprecated

### Fixed

- Fix LICENSE typo in setup.py
- Remove erroneous kwargs from write_holding_register()

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
