import logging
import sys

from loguru import logger

from app.common.middleware import request_id_var

_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name: <40}</cyan> | "
    "<yellow>{extra[request_id]: <36}</yellow> | "
    "{message}"
)

_NOISY_LOGGERS = ("httpx", "httpcore", "uvicorn.access", "google_genai")


class InterceptHandler(logging.Handler):
    """Redirect stdlib logging records to loguru, injecting request_id from context."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(request_id=request_id_var.get("-")).opt(
            depth=depth, exception=record.exc_info
        ).log(level, record.getMessage())


def configure_logging(level: str) -> None:
    logger.configure(extra={"request_id": "-"})
    logger.remove()
    logger.add(sys.stdout, level=level, format=_FORMAT, colorize=True)

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
