from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from bankin_platform.config import settings


def configure_logging() -> None:
    """
    Logging JSON = standard production (ELK/OpenSearch/CloudWatch).
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    handler.setFormatter(formatter)

    root.handlers = [handler]

