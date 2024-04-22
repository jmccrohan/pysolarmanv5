"""This is a Python module to interact with Solarman (IGEN-Tech) v5 based solar
inverter data loggers"""

from pysolarmanv5.pysolarmanv5 import PySolarmanV5
from pysolarmanv5.pysolarmanv5_async import PySolarmanV5Async
from pysolarmanv5.pysolarmanv5 import V5FrameError
from pysolarmanv5.pysolarmanv5 import NoSocketAvailableError

name = "pysolarmanv5"  # pylint: disable=invalid-name (C0103)

__all__ = [
    "PySolarmanV5",
    "PySolarmanV5Async",
    "V5FrameError",
    "NoSocketAvailableError",
]
