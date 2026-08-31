import json
import logging
from logging import LogRecord

from concurrent_log_handler import (
    ConcurrentRotatingFileHandler,
)  # pip install concurrent-log-handler


class ExtraFormatter(logging.Formatter):
    def format(self, record: LogRecord):
        standard = LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        ).__dict__.keys()

        extra = {
            key: value for key, value in record.__dict__.items() if key not in standard
        }

        record.extra_all = json.dumps(extra, ensure_ascii=False)
        return super().format(record)


formatter = ExtraFormatter(
    "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s | extra=%(extra_all)s ",
    "%Y-%m-%d %H:%M:%S",
)

file_handler = ConcurrentRotatingFileHandler(
    "./staticfiles/logs/logs.log",
    maxBytes=4 * 1024 * 1024,  # 10 Mb
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])
