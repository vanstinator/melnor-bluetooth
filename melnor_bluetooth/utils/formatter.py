""" Logging Formatter """
import logging


class CustomFormatter(logging.Formatter):
    """Simple colored logging formatter for example code"""

    cyan = "\x1b[36;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    str_format = (
        "%(asctime)s %(levelname)s %(name)s (%(filename)s:%(lineno)d) -- %(message)s"
    )

    FORMATS = {
        logging.DEBUG: cyan + str_format + reset,
        logging.INFO: green + str_format + reset,
        logging.WARNING: yellow + str_format + reset,
        logging.ERROR: red + str_format + reset,
        logging.CRITICAL: bold_red + str_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
