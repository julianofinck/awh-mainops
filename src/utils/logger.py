import logging
import os
from pathlib import Path


def config_logger(
    entry_point__file__: str,
    level: str = "WARNING",
):
    """
    Configurate basic logger for ETLs

        DEBUG:
            Detailed information, typically of interest only
            when diagnosing problems.
        INFO:
            Confirmation that things are working as expected.
        WARNING:
            An indication that something unexpected happened,
            or indicative of some problem in the near future
            (e.g. ‘disk space low’). The software is still
            working as expected.
        ERROR:
            Due to a more serious problem, the software has
            not been able to perform some function.
        CRITICAL:
            A serious error, indicating that the program itself
            may be unable to continue running.

    Refer to: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    """

    root = logging.getLogger()

    # Formatter
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
    )

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)

    # File Handler
    LOG_VERZEICHNIS = Path(os.getenv("LOG_VERZEICHNIS", "logs/"))
    LOG_VERZEICHNIS.mkdir(exist_ok=True)
    file_path_name = Path(entry_point__file__).stem + ".log"
    file = LOG_VERZEICHNIS / file_path_name

    file_handler = logging.FileHandler(file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    root.setLevel(level)
