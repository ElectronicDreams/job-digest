import logging


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with a consistent format.

    The caller is responsible for setting the log level after loading config.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger
