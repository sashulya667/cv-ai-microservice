import logging
import sys

from app.common.middleware import StructuredLogFilter


def configure_logging(level: str) -> None:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(request_id)s | %(message)s"
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, defaults={"request_id": "-"}))
    handler.addFilter(StructuredLogFilter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
