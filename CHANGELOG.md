# Changelog

## [v2.0.1] - 2021-12-29

### Added

- Add Add write_multiple_holding_registers() - function code 16

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
