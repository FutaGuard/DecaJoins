import logging
import sys

from loguru import logger


def configure(level: str = "DEBUG") -> None:
    """Configure loguru logger and intercept standard logging."""

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                lvl = logger.level(record.levelname).name
            except ValueError:
                lvl = record.levelno  # type: ignore[assignment]
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore[assignment]
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(
                lvl, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logger.remove()
    logger.add(sys.stderr, level=level, colorize=True)
